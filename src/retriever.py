"""
retriever.py – Hybrid retrieval: BM25 + ChromaDB vector + knowledge graph.

Fuses lexical (BM25Okapi), semantic (Gemini embeddings via ChromaDB),
and structural (NetworkX graph) signals using Reciprocal Rank Fusion.
"""

from __future__ import annotations

import re
from typing import Any

from rank_bm25 import BM25Okapi

from src.config import TOP_K
from src.embedder import embed_query, get_all_documents, get_collection
from src.graph_builder import load_graph, query_graph


# ═════════════════════════════════════════════════════════════════════════════
#  Hybrid Retriever
# ═════════════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """Three-signal retriever with reciprocal-rank fusion."""

    # ── Initialisation ───────────────────────────────────────────────────

    def __init__(self) -> None:
        # Load every document from ChromaDB
        self.docs: list[dict[str, Any]] = get_all_documents()

        # Build BM25 index (lowercase tokenised)
        corpus = [
            doc["text"].lower().split() for doc in self.docs
        ]
        self.bm25 = BM25Okapi(corpus)

        # ChromaDB collection handle
        self.collection = get_collection()

        # Knowledge graph
        self.graph = load_graph()

        print(
            f"🔎 HybridRetriever ready  "
            f"({len(self.docs)} docs, "
            f"{self.graph.number_of_nodes()} graph nodes)"
        )

    # ── BM25 (lexical) ──────────────────────────────────────────────────

    def bm25_search(
        self, query: str, top_k: int = TOP_K,
    ) -> list[dict[str, Any]]:
        """Return the *top_k* BM25 hits for *query*."""
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)

        # Indices of top-k scores (descending)
        ranked = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True,
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

    # ── ChromaDB vector (semantic) ───────────────────────────────────────

    def vector_search(
        self,
        query: str,
        top_k: int = TOP_K,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the *top_k* nearest-neighbour hits from ChromaDB."""
        q_embedding = embed_query(query)

        kwargs: dict[str, Any] = {
            "query_embeddings": [q_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self.collection.query(**kwargs)

        results: list[dict[str, Any]] = []
        docs  = raw["documents"][0]       # single query → first list
        metas = raw["metadatas"][0]
        dists = raw["distances"][0]

        for rank, (text, meta, dist) in enumerate(
            zip(docs, metas, dists), 1,
        ):
            results.append({
                "text":     text,
                "metadata": meta,
                "score":    float(dist),
                "rank":     rank,
            })
        return results

    # ── Reciprocal Rank Fusion ───────────────────────────────────────────

    @staticmethod
    def reciprocal_rank_fusion(
        bm25_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        k: int = 60,
    ) -> list[dict[str, Any]]:
        """Merge two ranked lists using RRF (k = 60 by default).

        Each document is keyed by its first 100 characters to allow
        matching across the two result sets.
        """
        scores: dict[str, float] = {}
        doc_map: dict[str, dict[str, Any]] = {}

        for result_list in (bm25_results, vector_results):
            for item in result_list:
                key = item["text"][:100]
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

    # ── ChromaDB metadata filter builder ─────────────────────────────────

    @staticmethod
    def build_where_filter(
        os: str | None = None,
        difficulty: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a ChromaDB ``$and`` filter from optional params.

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
    def detect_query_intent(query: str) -> dict[str, Any]:
        """Lightweight intent extraction from the raw query string."""
        q = query.lower()

        # OS
        if "windows" in q:
            os_val = "windows"
        elif "linux" in q:
            os_val = "linux"
        else:
            os_val = None

        # Difficulty
        diff_val = None
        for d in ("insane", "hard", "medium", "easy"):
            if re.search(rf"\b{d}\b", q):
                diff_val = d
                break

        # Query type
        structured_signals = [
            "cheatsheet", "list", "which machine",
            "all machines", "where",
        ]
        query_type = (
            "structured"
            if any(sig in q for sig in structured_signals)
            else "semantic"
        )

        return {
            "os": os_val,
            "difficulty": diff_val,
            "query_type": query_type,
        }

    # ── Main retrieve entry-point ────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K,
        os_filter: str | None = None,
        difficulty_filter: str | None = None,
    ) -> dict[str, Any]:
        """Run the full hybrid retrieval pipeline.

        Returns::

            {
                "chunks":          [merged top-k dicts],
                "graph":           {matched_categories, …, relevant_machines},
                "query":           original query string,
                "filters_applied": {"os": …, "difficulty": …},
            }
        """
        # Intent detection
        intent = self.detect_query_intent(query)

        os_val   = os_filter   or intent["os"]
        diff_val = difficulty_filter or intent["difficulty"]

        where = self.build_where_filter(os_val, diff_val)

        # Three retrieval channels
        bm25_hits   = self.bm25_search(query, top_k=top_k * 2)
        vector_hits = self.vector_search(query, top_k=top_k * 2, where=where)
        graph_hits  = query_graph(self.graph, query)

        # Fuse BM25 + vector
        merged = self.reciprocal_rank_fusion(bm25_hits, vector_hits)[:top_k]

        return {
            "chunks":          merged,
            "graph":           graph_hits,
            "query":           query,
            "filters_applied": {"os": os_val, "difficulty": diff_val},
        }
