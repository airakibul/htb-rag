"""
intent_router.py – Generalized Neural Semantic Intent Router.

Concrete implementation of IntentClassifier using locally-cached
SentenceTransformer embeddings (all-MiniLM-L6-v2) and anchor centroid
cosine-similarity classification. Replaces fragile regexes with robust
semantic intent understanding.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import numpy as np

from src.domain.interfaces import IntentClassifier

logger = logging.getLogger(__name__)

# Singleton cached instance
_intent_router_instance: Any = None


class SemanticIntentRouter(IntentClassifier):
    """Zero-shot / exemplar-based semantic intent classifier."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model: Any = None
        try:
            from sentence_transformers import SentenceTransformer

            try:
                self.model = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                try:
                    # Fallback to local name without prefix
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
        # Generalized, domain-agnostic semantic archetypes (no test-set memorization)
        broad_exemplars = [
            "Comprehensive cheatsheet of techniques",
            "Overview and summary of common attack methods",
            "Catalog of vulnerabilities and vectors across multiple targets",
            "General reference guide and attack taxonomy",
            "Collection of privilege escalation paths across systems",
            "Compilation of reconnaissance and enumeration strategies",
            "Taxonomy of offensive tools and mechanisms",
            "Broad survey of lateral movement options across hosts",
            "Handbook of common offensive security techniques",
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

        # Clean explicit intent checks
        has_cve = bool(re.search(r"\bcve-\d{4}-\d+\b", low)) or bool(re.search(r"\bms\d{2}-\d{3}\b", low))
        has_cheatsheet_intent = bool(re.search(r"\b(?:cheat\s*sheet|catalog|overview|handbook|summary|reference\s+guide|compilation)\b", low))

        if has_cheatsheet_intent:
            scope = "broad"
            broad_sim, specific_sim = 1.0, 0.0
        elif has_cve:
            scope = "specific"
            broad_sim, specific_sim = 0.0, 1.0
        else:
            # Multi-prototype / k-NN exemplar matching (average top 3 similarities)
            # Prevents high-bias underfitting caused by single-centroid averaging
            q_emb = self._encode_texts([query])[0]
            broad_scores = np.dot(self.broad_emb, q_emb)
            specific_scores = np.dot(self.specific_emb, q_emb)

            broad_sim = float(np.mean(np.sort(broad_scores)[-3:]))
            specific_sim = float(np.mean(np.sort(specific_scores)[-3:]))

            scope = "broad" if broad_sim > specific_sim else "specific"

        # Target OS detection (generalized domain entity mapping)
        windows_indicators = [
            "windows", "active directory", "adcs", "winrm", "powershell",
            "kerberos", "ntlm", "rdp", "winpeas", "ms17-010",
            "mimikatz", "cmd.exe", "powershell.exe", "activedirectory",
        ]
        linux_indicators = [
            "linux", "suid", "gtfobins", "sudo", "bash", "linpeas",
            "cron", "polkit", "elf", "nfs", "systemctl", "sudoers", "samba",
        ]

        has_win = any(re.search(rf"\b{re.escape(w)}\b", low) for w in windows_indicators)
        has_lin = any(re.search(rf"\b{re.escape(w)}\b", low) for w in linux_indicators)
        if has_win and not has_lin:
            target_os = "windows"
        elif has_lin and not has_win:
            target_os = "linux"
        else:
            target_os = None

        # Target Phase detection (aligned with standard offensive lifecycle)
        if any(w in low for w in ["privilege escalation", "privesc", "priv esc", "elevat"]):
            target_phase = "privesc"
        elif any(w in low for w in ["lateral movement", "pivot", "pivoting"]):
            target_phase = "lateral_movement"
        elif any(w in low for w in ["foothold", "initial access", "initial compromise"]):
            target_phase = "foothold"
        elif any(w in low for w in ["recon", "reconnaissance", "enumeration", "port scan", "scanning"]):
            target_phase = "recon"
        elif any(w in low for w in ["credential", "password cracking", "hash dump"]):
            target_phase = "credential_access"
        elif any(w in low for w in ["persistence", "backdoor", "scheduled task"]):
            target_phase = "persistence"
        else:
            target_phase = None

        return {
            "scope": scope,
            "target_os": target_os,
            "target_phase": target_phase,
            "scores": {"broad": broad_sim, "specific": specific_sim},
        }


def get_intent_router() -> SemanticIntentRouter:
    """Return the singleton instance of SemanticIntentRouter."""
    global _intent_router_instance
    if _intent_router_instance is None:
        _intent_router_instance = SemanticIntentRouter()
    return _intent_router_instance
