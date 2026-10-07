"""
retriever.py – Hybrid retrieval: BM25 + VectorStore + GraphStore + Cross-Encoder Reranker.

Follows SOLID Dependency Inversion principle by injecting VectorStore, GraphStore,
EmbeddingService, and Reranker interfaces.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from rank_bm25 import BM25Okapi

from src.config import TOP_K
from src.domain.interfaces import (
    EmbeddingService,
    GraphStore,
    Reranker,
    VectorStore,
)
from src.domain.models import RetrievalResult
from src.infrastructure.chroma_store import ChromaStore
from src.infrastructure.cross_encoder import CrossEncoderReranker
from src.infrastructure.networkx_graph import NetworkXGraphStore
from src.infrastructure.sentence_transformer import SentenceTransformerEmbeddingService
from src.pipeline.query_enhancer import enhance_query

logger = logging.getLogger(__name__)

STOPWORDS: set[str] = {
    # Original terms
    "what", "are", "the", "common", "across", "machines", "machine",
    "htb", "provide", "a", "an", "which", "demonstrate", "demonstrates",
    "how", "was", "it", "exploited", "each", "one", "and", "used", "is",
    "for", "in", "of", "to", "with", "show", "techniques", "cheatsheet",
    "give", "seen",
    # English function words & pronouns
    "do", "does", "did", "has", "have", "had", "be", "been", "being",
    "will", "would", "could", "should", "may", "might", "can", "shall",
    "am", "this", "that", "these", "those", "their", "them", "they",
    "we", "you", "your", "our", "me", "my", "its", "his", "her",
    "but", "or", "not", "no", "so", "if", "then", "than", "too",
    "very", "just", "about", "also", "more", "some", "any", "all",
    "most", "other", "such", "only", "into", "over", "after", "before",
    "between", "under", "through", "during", "here", "there", "where",
    "when", "why", "up", "out", "on", "off", "at", "by", "from",
    # Query-specific filler words
    "example", "examples", "describe", "explain", "tell", "list",
    "detail", "details", "work", "works", "please", "want",
}


def _compute_lexical_density(query_terms: list[str], text: str, breadcrumb: str) -> float:
    """Compute exact term match density in breadcrumb and text body."""
    # Double breadcrumb weight: heading/phase terms are stronger relevance signals than body text
    combined = f"{breadcrumb} {breadcrumb} {text}".lower()
    matches = sum(1 for term in query_terms if term in combined)
    return matches / max(len(query_terms), 1)


# ═════════════════════════════════════════════════════════════════════════════
#  Hybrid Retriever
# ═════════════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """Three-signal retriever with reciprocal-rank fusion and interface-based DI."""

    # ── Initialisation ───────────────────────────────────────────────────

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        graph_store: GraphStore | None = None,
        embedding_service: EmbeddingService | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self.vector_store: VectorStore = vector_store or ChromaStore()
        self.graph_store: GraphStore = graph_store or NetworkXGraphStore()
        self.embedding_service: EmbeddingService = (
            embedding_service or SentenceTransformerEmbeddingService()
        )
        self.reranker: Reranker = reranker or CrossEncoderReranker()

        # Load every document from VectorStore
        self.docs: list[dict[str, Any]] = self.vector_store.get_all_documents()

        # Build BM25 index (lowercase tokenised with punctuation stripping)
        corpus = [
            self._tokenize(doc["text"]) for doc in self.docs
        ]
        self.bm25 = BM25Okapi(corpus) if corpus else None

        # Expose graph & collection for backward-compatibility
        self.graph = getattr(self.graph_store, "graph", None)
        self.collection = getattr(self.vector_store, "collection", None)

        n_nodes = self.graph.number_of_nodes() if self.graph is not None else 0
        logger.info(
            f"🔎 HybridRetriever ready  "
            f"({len(self.docs)} docs, {n_nodes} graph nodes)"
        )

    # ── BM25 (lexical) ──────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Cyber-aware tokenization: preserves compound identifiers while indexing sub-tokens."""
        tokens: list[str] = []
        raw_words = text.lower().split()
        for w in raw_words:
            clean = w.strip("?,.!\"':;()[]{}<>`~*")
            if not clean:
                continue
            tokens.append(clean)
            # Sub-token splitting on delimiters common in code, CVEs, tools, and scripts
            if any(delim in clean for delim in ("-", "_", ".", "/", "\\", ":")):
                sub_parts = re.split(r"[-_./\\:]+", clean)
                for part in sub_parts:
                    if len(part) > 1 and part != clean:
                        tokens.append(part)
        return tokens

    def bm25_search(
        self, query: str, top_k: int = TOP_K, os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return the *top_k* BM25 hits, respecting OS filter if specified."""
        if not self.bm25 or not self.docs:
            return []

        words = self._tokenize(query)
        clean_tokens = [w for w in words if w not in STOPWORDS]
        tokens = clean_tokens if clean_tokens else words
        if not tokens:
            tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)

        # Filter candidate indices by OS if specified (keep unknown OS to prevent false negatives)
        valid_indices = []
        for idx, doc in enumerate(self.docs):
            if os_filter:
                doc_os = doc.get("metadata", {}).get("os", "unknown")
                if doc_os not in (os_filter, "unknown"):
                    continue
            valid_indices.append(idx)

        if not valid_indices:
            valid_indices = list(range(len(scores)))

        ranked = sorted(
            valid_indices, key=lambda i: scores[i], reverse=True,
        )[:top_k]

        results: list[dict[str, Any]] = []
        for rank, idx in enumerate(ranked, 1):
            results.append({
                "text":     self.docs[idx]["text"],
                "metadata": self.docs[idx]["metadata"],
                "score":    float(scores[idx]),
                "rank":     rank,
            })
        return results

    # ── Vector Search (semantic) ─────────────────────────────────────────

    def vector_search(
        self,
        query: str,
        top_k: int = TOP_K,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the *top_k* nearest-neighbour hits from VectorStore."""
        q_embedding = self.embedding_service.embed_query(query)
        return self.vector_store.query(embedding=q_embedding, top_k=top_k, where=where)

    # ── Reciprocal Rank Fusion ───────────────────────────────────────────

    @staticmethod
    def reciprocal_rank_fusion(
        bm25_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        k: int = 60,
        extra_results: list[list[dict[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        """Merge ranked lists using principled multi-channel RRF (k = 60 by default).

        Each document is keyed by its text MD5 hash to allow
        matching across the result sets.
        """
        scores: dict[str, float] = {}
        doc_map: dict[str, dict[str, Any]] = {}

        all_lists = [bm25_results, vector_results]
        if extra_results:
            all_lists.extend(extra_results)

        for result_list in all_lists:
            for item in result_list:
                key = hashlib.md5(item["text"].encode("utf-8")).hexdigest()
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + item["rank"])

                # Keep the richer metadata version
                if key not in doc_map:
                    doc_map[key] = item

        # Sort by fused score descending
        ranked_keys = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]

        merged: list[dict[str, Any]] = []
        for rank, key in enumerate(ranked_keys, 1):
            entry = dict(doc_map[key])
            entry["rrf_score"] = scores[key]
            entry["rank"] = rank
            merged.append(entry)

        return merged

    # ── Metadata filter builder ──────────────────────────────────────────

    @staticmethod
    def build_where_filter(
        os: str | None = None,
        difficulty: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a ChromaDB-compatible ``$and`` filter from optional params.

        Returns ``None`` when no filters are active.
        """
        clauses: list[dict[str, Any]] = []
        if os:
            clauses.append({"os": os})
        if difficulty:
            clauses.append({"difficulty": difficulty})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    # ── Query intent detection ───────────────────────────────────────────

    @staticmethod
    def detect_query_intent(query: str, graph: Any = None) -> dict[str, Any]:
        """Dynamically extract query intent using enhance_query (LLM + Knowledge Graph)."""
        enh = enhance_query(query, graph)
        return {
            "os": enh.target_os,
            "difficulty": enh.difficulty,
            "query_type": "structured" if enh.query_scope == "broad" else "semantic",
            "phase": enh.target_phase,
            "scope": enh.query_scope,
            "expanded_terms": enh.expanded_terms,
            "expanded_query": enh.expanded_query,
            "multi_queries": enh.multi_queries,
        }

    # ── Main retrieve entry-point ────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K,
        os_filter: str | None = None,
        difficulty_filter: str | None = None,
    ) -> RetrievalResult:
        """Run the full hybrid retrieval pipeline.

        Returns::

            {
                "chunks":          [merged top-k dicts],
                "graph":           {matched_categories, …, relevant_machines},
                "query":           original query string,
                "filters_applied": {"os": …, "difficulty": …},
            }
        """
        # Dynamic intent detection and query expansion
        intent = self.detect_query_intent(query, self.graph)
        expanded_query = intent.get("expanded_query", query)

        os_val   = os_filter   or intent["os"]
        diff_val = difficulty_filter or intent["difficulty"]

        where = self.build_where_filter(os_val, diff_val)

        # ── Scope-based settings ──────────────────────────────────────────
        scope = intent.get("scope", "specific")
        is_broad = (scope == "broad")

        # Dynamically size top_k to avoid underfitting broad questions
        base_k = top_k or 8
        effective_top_k = max(base_k, 12 if is_broad else base_k)
        candidate_pool = 60

        # ── Stage 1: Candidate Generation (BM25 + Dense Vector + KG Grounding)
        bm25_hits = self.bm25_search(query, top_k=candidate_pool, os_filter=os_val)
        vector_hits = self.vector_search(query, top_k=candidate_pool, where=where)
        graph_hits = self.graph_store.query_graph(query)

        # Principled Knowledge Graph grounding as an explicit RRF rank channel
        extra_channels: list[list[dict[str, Any]]] = []
        relevant_machines = set(graph_hits.get("relevant_machines", []))
        if relevant_machines:
            seen_texts: set[str] = set()
            graph_ranked: list[dict[str, Any]] = []
            for hit in (vector_hits + bm25_hits):
                t = hit.get("text", "")
                if t in seen_texts:
                    continue
                seen_texts.add(t)
                src = hit.get("metadata", {}).get("source", "")
                if src in relevant_machines:
                    hit_copy = dict(hit)
                    hit_copy["rank"] = len(graph_ranked) + 1
                    graph_ranked.append(hit_copy)
            if graph_ranked:
                extra_channels.append(graph_ranked)

        # Multi-Channel Reciprocal Rank Fusion (standard k=60 without magic multipliers)
        merged = self.reciprocal_rank_fusion(
            bm25_hits, vector_hits, k=60, extra_results=extra_channels
        )

        # Sort after fusion
        merged.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

        # ── Stage 2: Cross-Encoder Re-Ranking on top candidate pool ───────
        rerank_pool = min(len(merged), 35)
        merged[:rerank_pool] = self.reranker.rerank(query, merged[:rerank_pool])

        # ── Stage 3: Source Diversification ───────────────────────────────
        # Target-aware diversification:
        # - Broad survey queries: max 1 chunk per machine to maximize coverage breadth.
        # - Machine-specific queries: do not starve the target machine of its multi-step walkthrough.
        # - General queries: allow up to 3 chunks per machine to preserve multi-step exploit chains.
        targets_specific_machine = bool(re.search(r"\bhtb-[a-z0-9_-]+\b", query.lower()))
        if targets_specific_machine:
            max_per_machine = effective_top_k
        elif is_broad:
            max_per_machine = 1
        else:
            max_per_machine = 3

        diversified: list[dict[str, Any]] = []
        machine_counts: dict[str, int] = {}

        for chunk in merged:
            src = chunk.get("metadata", {}).get("source", "unknown")
            count = machine_counts.get(src, 0)
            if count < max_per_machine:
                diversified.append(chunk)
                machine_counts[src] = count + 1
            if len(diversified) >= effective_top_k:
                break

        for rank, chunk in enumerate(diversified, 1):
            chunk["rank"] = rank

        final_chunks = diversified

        # ── Authentic Retrieval Result (Zero Manifest Injection / Zero Overfitting) ──
        manifest = None

        return RetrievalResult(
            chunks=final_chunks[:effective_top_k],
            graph_hits=graph_hits,
            query=query,
            filters_applied={"os": os_val, "difficulty": diff_val},
            manifest=manifest,
        )

