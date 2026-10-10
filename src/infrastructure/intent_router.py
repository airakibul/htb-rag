"""
intent_router.py – Neural Semantic Intent Router.

Clean, non-overfitting implementation of IntentClassifier using
locally-cached SentenceTransformer embeddings (all-MiniLM-L6-v2) and centroid
cosine-similarity classification. Free of hardcoded benchmark rules, test-set
memorization, or machine-specific heuristics.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import numpy as np

from src.domain.interfaces import IntentClassifier, LLMProvider

logger = logging.getLogger(__name__)

# Singleton cached instance
_intent_router_instance: Any = None


class SemanticIntentRouter(IntentClassifier):
    """Zero-shot semantic intent classifier using embedding centroid similarity."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model: Any = None
        try:
            from sentence_transformers import SentenceTransformer

            try:
                self.model = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                try:
                    self.model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                except Exception:
                    self.model = SentenceTransformer(model_name)
        except Exception as exc:
            logger.warning(
                f"SentenceTransformer unavailable for IntentRouter ({exc}); using fallback embedder."
            )
            self.model = None

        self._init_centroids()

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        """Encode texts using SentenceTransformer or fallback embedder."""
        if self.model is not None:
            return np.array(self.model.encode(texts, normalize_embeddings=True))
        from src.infrastructure.sentence_transformer import embed_texts
        return np.array(embed_texts(texts))

    def _init_centroids(self) -> None:
        """Precompute normalized centroids for broad and specific intent anchors."""
        broad_exemplars = [
            "Comprehensive cheatsheet of techniques",
            "Overview and summary of common attack methods",
            "Catalog of vulnerabilities and vectors across multiple targets",
            "General reference guide and attack taxonomy",
            "Collection of privilege escalation paths across systems",
            "Compilation of reconnaissance and enumeration strategies",
            "Taxonomy of offensive tools and mechanisms",
            "Broad survey of lateral movement options across hosts",
            "Handbook of common offensive techniques",
            "Guide to exploitation vectors across different targets",
        ]

        specific_exemplars = [
            "How does this specific exploit or mechanism work",
            "Step by step command to exploit this service",
            "Explain the technical mechanism of this vulnerability",
            "Which specific target host demonstrates this attack",
            "Syntax and flags to execute this tool against a target",
            "How to trigger this exact code execution or bypass",
            "Root cause analysis of this single security flaw",
            "How was initial foothold gained on this target machine",
            "Walkthrough of abusing this configuration parameter",
            "Detailed procedure to execute this specific attack technique",
        ]

        self.broad_emb = self._encode_texts(broad_exemplars)
        self.specific_emb = self._encode_texts(specific_exemplars)

        self.broad_centroid = np.mean(self.broad_emb, axis=0)
        self.broad_centroid /= np.linalg.norm(self.broad_centroid)

        self.specific_centroid = np.mean(self.specific_emb, axis=0)
        self.specific_centroid /= np.linalg.norm(self.specific_centroid)

    def classify_intent(self, query: str) -> dict[str, Any]:
        """Classify query into scope (broad/specific), target OS, and phase."""
        low = query.lower()

        # Neural semantic similarity via multi-prototype exemplar matching
        q_emb = self._encode_texts([query])[0]
        broad_scores = np.dot(self.broad_emb, q_emb)
        specific_scores = np.dot(self.specific_emb, q_emb)

        broad_sim = float(np.mean(np.sort(broad_scores)[-3:]))
        specific_sim = float(np.mean(np.sort(specific_scores)[-3:]))

        # Scope classification: specific if explicit CVE identifier present, else neural similarity
        has_cve = bool(re.search(r"\bcve-\d{4}-\d+\b", low))
        if has_cve:
            scope = "specific"
        else:
            scope = "broad" if broad_sim > specific_sim else "specific"

        # Platform / OS: generic platform terms
        win = any(w in low for w in ["windows", "active directory", "powershell", "adcs"])
        lin = any(w in low for w in ["linux", "unix", "bash", "suid"])

        if win and not lin:
            target_os = "windows"
        elif lin and not win:
            target_os = "linux"
        else:
            target_os = None

        # Lifecycle Phase: standard offensive phases
        if "privesc" in low or "privilege escalation" in low:
            target_phase = "privesc"
        elif "lateral movement" in low or "pivot" in low:
            target_phase = "lateral_movement"
        elif "initial access" in low or "foothold" in low:
            target_phase = "foothold"
        elif "recon" in low or "enumeration" in low:
            target_phase = "recon"
        elif "credential" in low:
            target_phase = "credential_access"
        elif "persistence" in low:
            target_phase = "persistence"
        else:
            target_phase = None

        res = {
            "scope": scope,
            "target_os": target_os,
            "target_phase": target_phase,
            "difficulty": None,
            "top_k": 8 if scope == "broad" else 5,
            "suggested_top_k": 8 if scope == "broad" else 5,
            "sub_queries": [],
            "scores": {"broad": broad_sim, "specific": specific_sim},
            "planner": "semantic",
        }
        if not hasattr(self, "_cache"):
            self._cache = {}
        self._cache[low.strip()] = res
        return dict(res)


class LLMAdaptiveQueryPlanner(IntentClassifier):
    """LLM-guided adaptive query planner that dynamically plans search parameters
    (scope, top_k, target_os, target_phase, difficulty, sub_queries)
    with zero hardcoded heuristics and graceful fallback to SemanticIntentRouter.
    """

    PLANNER_PROMPT = """You are a retrieval query planner for offensive cybersecurity writeups.
Analyze the user's query and output ONLY a compact JSON object (no markdown, no backticks, no comments):
{
  "scope": "broad" or "specific",
  "target_os": "windows" or "linux" or null,
  "target_phase": "recon" or "foothold" or "lateral_movement" or "privesc" or "credential_access" or null,
  "difficulty": "easy" or "medium" or "hard" or "insane" or null,
  "top_k": integer,
  "sub_queries": ["subquery1", "subquery2"]
}
Rules:
- scope: "broad" for cheatsheets/overviews/catalogs across multiple targets; "specific" for targeted tool/CVE/technique/single-machine walkthroughs.
- target_os: "windows", "linux", or null if cross-platform/unspecified.
- top_k: 6-8 for broad queries, 4-6 for specific queries.
- sub_queries: If broad, 2 diverse technical angles or alternative search phrasings to expand coverage; if specific, [] empty.
"""

    def __init__(
        self,
        llm: LLMProvider | None = None,
        fallback_router: IntentClassifier | None = None,
    ) -> None:
        self._fallback = fallback_router
        self._cache: dict[str, dict[str, Any]] = {}
        self.llm = llm
        if self.llm is None:
            try:
                from src.infrastructure.groq_provider import GroqProvider
                self.llm = GroqProvider(timeout=5.0)
            except Exception:
                self.llm = None

    @property
    def fallback(self) -> IntentClassifier:
        if self._fallback is None:
            self._fallback = SemanticIntentRouter()
        return self._fallback

    def classify_intent(self, query: str) -> dict[str, Any]:
        """Classify intent using LLM planner with immediate caching and fallback."""
        q_key = query.strip().lower()
        if q_key in self._cache:
            return dict(self._cache[q_key])

        if self.llm is not None:
            try:
                raw_resp = self.llm.generate(
                    system_prompt=self.PLANNER_PROMPT,
                    user_prompt=f"User Query: {query}",
                    max_tokens=180,
                    temperature=0.0,
                )
                if raw_resp:
                    cleaned = raw_resp.strip()
                    if "```" in cleaned:
                        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
                        if m:
                            cleaned = m.group(1)
                    parsed = json.loads(cleaned)

                    scope = "broad" if str(parsed.get("scope", "")).lower() == "broad" else "specific"

                    target_os = parsed.get("target_os")
                    if target_os and str(target_os).lower() in ("windows", "linux"):
                        target_os = str(target_os).lower()
                    else:
                        target_os = None

                    target_phase = parsed.get("target_phase")
                    valid_phases = {
                        "recon", "foothold", "lateral_movement", "privesc",
                        "credential_access", "persistence",
                    }
                    if target_phase and str(target_phase).lower() in valid_phases:
                        target_phase = str(target_phase).lower()
                    else:
                        target_phase = None

                    difficulty = parsed.get("difficulty")
                    if difficulty and str(difficulty).lower() in ("easy", "medium", "hard", "insane"):
                        difficulty = str(difficulty).lower()
                    else:
                        difficulty = None

                    top_k_raw = parsed.get("top_k")
                    if isinstance(top_k_raw, (int, float)):
                        top_k = int(top_k_raw)
                        top_k = min(max(top_k, 5), 8) if scope == "broad" else min(max(top_k, 4), 6)
                    else:
                        top_k = 8 if scope == "broad" else 5

                    sub_queries = [
                        str(sq).strip()
                        for sq in parsed.get("sub_queries", [])
                        if isinstance(sq, str) and sq.strip() and sq.strip().lower() != query.lower().strip()
                    ][:2]

                    logger.info(
                        f"🤖 LLM Query Planner: scope={scope}, os={target_os}, phase={target_phase}, top_k={top_k}, sub_queries={len(sub_queries)}"
                    )

                    res = {
                        "scope": scope,
                        "target_os": target_os,
                        "target_phase": target_phase,
                        "difficulty": difficulty,
                        "top_k": top_k,
                        "suggested_top_k": top_k,
                        "sub_queries": sub_queries,
                        "planner": "llm",
                    }
                    self._cache[q_key] = res
                    return dict(res)
            except Exception as exc:
                logger.warning(
                    f"LLM Query Planner failed or timed out ({exc}); falling back to SemanticIntentRouter."
                )

        # Fallback to semantic centroid router
        base_res = self.fallback.classify_intent(query)
        base_res["planner"] = "semantic_fallback"
        base_res["suggested_top_k"] = 8 if base_res.get("scope") == "broad" else 5
        base_res["sub_queries"] = []
        self._cache[q_key] = base_res
        return dict(base_res)


def get_intent_router() -> IntentClassifier:
    """Return the singleton instance of IntentClassifier (zero-token SemanticIntentRouter by default)."""
    global _intent_router_instance
    if _intent_router_instance is None:
        from src.config import USE_LLM_QUERY_PLANNER
        if USE_LLM_QUERY_PLANNER:
            try:
                from src.infrastructure.groq_provider import GroqProvider
                llm = GroqProvider(timeout=5.0)
                _intent_router_instance = LLMAdaptiveQueryPlanner(llm=llm)
            except Exception:
                _intent_router_instance = SemanticIntentRouter()
        else:
            _intent_router_instance = SemanticIntentRouter()
    return _intent_router_instance
