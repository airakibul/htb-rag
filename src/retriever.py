"""
retriever.py – Hybrid retrieval: BM25 + ChromaDB vector + knowledge graph.

Fuses lexical (BM25Okapi), semantic (Gemini embeddings via ChromaDB),
and structural (NetworkX graph) signals using Reciprocal Rank Fusion.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from rank_bm25 import BM25Okapi

from src.config import TOP_K
from src.embedder import embed_query, get_all_documents, get_collection
from src.graph_builder import load_graph, query_graph
from src.query_enhancer import enhance_query

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

        logger.info(
            f"🔎 HybridRetriever ready  "
            f"({len(self.docs)} docs, "
            f"{self.graph.number_of_nodes()} graph nodes)"
        )


    # ── BM25 (lexical) ──────────────────────────────────────────────────

    def bm25_search(
        self, query: str, top_k: int = TOP_K, os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return the *top_k* BM25 hits, respecting OS filter if specified."""
        words = [w.strip("?,.!\"':;") for w in query.lower().split()]
        clean_tokens = [w for w in words if w and w not in STOPWORDS]
        tokens = clean_tokens if clean_tokens else [w for w in words if w]
        if not tokens:
            tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)

        # Filter candidate indices by OS if specified
        valid_indices = []
        for idx, doc in enumerate(self.docs):
            if os_filter:
                doc_os = doc.get("metadata", {}).get("os", "unknown")
                if doc_os != os_filter:
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
        # Dynamic intent detection and query expansion
        intent = self.detect_query_intent(query, self.graph)
        expanded_query = intent.get("expanded_query", query)

        os_val   = os_filter   or intent["os"]
        diff_val = difficulty_filter or intent["difficulty"]

        where = self.build_where_filter(os_val, diff_val)

        q_lower = query.lower()

        # ── Scope-based Top-K and Candidate Pool ────────────────────────────
        scope = intent.get("scope", "specific")
        is_broad = (scope == "broad")

        if is_broad:
            effective_top_k = max(top_k, 25)
            candidate_pool = 100
        else:
            effective_top_k = min(top_k, 8) if top_k else 6
            candidate_pool = 35

        # Three retrieval channels
        bm25_hits   = self.bm25_search(expanded_query, top_k=candidate_pool, os_filter=os_val)
        vector_hits = self.vector_search(expanded_query, top_k=candidate_pool, where=where)
        graph_hits  = query_graph(self.graph, query)

        # Fuse BM25 + vector
        merged = self.reciprocal_rank_fusion(bm25_hits, vector_hits, k=60)

        # Phase Boost: boost chunks matching target attack phase in metadata or breadcrumb
        target_phase = intent.get("phase")
        if target_phase:
            for chunk in merged:
                meta = chunk.get("metadata", {})
                chunk_phase = meta.get("attack_phase", "").lower()
                bc = meta.get("breadcrumb", "").lower()
                if chunk_phase == target_phase or target_phase in bc:
                    chunk["rrf_score"] = chunk.get("rrf_score", 0.0) * 1.4

        # Specific CVE Boost: exact match in cve_ids gets 5x score
        target_cves = {c.upper() for c in re.findall(r"cve-\d{4}-\d+", q_lower)}
        for term in intent.get("expanded_terms", []) + graph_hits.get("matched_cves", []):
            for cve in re.findall(r"cve-\d{4}-\d+", str(term), re.IGNORECASE):
                target_cves.add(cve.upper())

        if target_cves:
            for chunk in merged:
                chunk_cves = str(chunk.get("metadata", {}).get("cve_ids", "")).upper()
                if any(tc in chunk_cves for tc in target_cves):
                    chunk["rrf_score"] = chunk.get("rrf_score", 0.0) * 5.0

        # Graph Boost: apply 1.5x score boost to chunks whose source is in graph_hits["relevant_machines"]
        relevant_machines = set(graph_hits.get("relevant_machines", []))
        if relevant_machines:
            for chunk in merged:
                src = chunk.get("metadata", {}).get("source", "")
                if src in relevant_machines:
                    chunk["rrf_score"] = chunk.get("rrf_score", 0.0) * 1.5


        # ── OS Enforcement for Broad Queries ────────────────────────────────
        # When intent detects a specific OS (e.g., "windows" or "linux"),
        # remove chunks from other OSes to prevent off-topic results.
        if is_broad and os_val:
            os_lower = os_val.lower()
            os_filtered = [
                c for c in merged
                if c.get("metadata", {}).get("os", "unknown").lower() in (os_lower, "unknown")
            ]
            # Only apply if we still have enough results
            if len(os_filtered) >= effective_top_k:
                merged = os_filtered

        # ── Step 3: Fast Lexical-Semantic Re-Ranking ────────────────────────
        query_keywords = [
            w.strip(".") for w in re.findall(r'[A-Za-z0-9_\-\.]+', q_lower)
            if len(w.strip(".")) > 2 and w.strip(".") not in STOPWORDS
        ]
        if query_keywords and merged:
            max_rrf = max((c.get("rrf_score", 0.0) for c in merged), default=1.0)
            if max_rrf <= 0:
                max_rrf = 1.0
            for item in merged:
                chunk_meta = item.get("metadata", {})
                density = _compute_lexical_density(
                    query_keywords,
                    item.get("text", ""),
                    chunk_meta.get("breadcrumb", "")
                )
                norm_score = item.get("rrf_score", 0.0) / max_rrf
                combined_score = norm_score * 0.7 + density * 0.3
                item["score"] = combined_score
                item["rrf_score"] = combined_score

        merged.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

        # ── Cross-Encoder Re-Ranking ──────────────────────────────────────
        from src.reranker import rerank
        rerank_pool = min(len(merged), 15)
        merged[:rerank_pool] = rerank(query, merged[:rerank_pool])


        # Source Diversification: allow max 1 chunk per machine for broad queries (max 2 for specific)

        max_per_machine = 1 if is_broad else 2
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

        # Re-rank
        for rank, chunk in enumerate(diversified, 1):
            chunk["rank"] = rank

        # Dynamic Relative Score-Drop Thresholding (Cross-Encoder Cutoff)
        final_chunks = diversified
        if not is_broad and len(final_chunks) > 1:
            if "ce_score" in final_chunks[0]:
                top_ce = final_chunks[0]["ce_score"]
                kept = [final_chunks[0]]
                for prev, curr in zip(final_chunks[:-1], final_chunks[1:]):
                    prev_ce = prev.get("ce_score", top_ce)
                    curr_ce = curr.get("ce_score", top_ce)
                    # If total drop from top exceeds 4.5 or cliff drop from previous exceeds 3.0, cut off
                    if (top_ce - curr_ce > 4.5) or (prev_ce - curr_ce > 3.0):
                        break
                    kept.append(curr)
                final_chunks = kept
            else:
                top_score = final_chunks[0].get("rrf_score", 0.0)
                final_chunks = [c for c in final_chunks if c.get("rrf_score", 0.0) >= top_score * 0.50]

        return {
            "chunks":          final_chunks[:effective_top_k],
            "graph":           graph_hits,
            "query":           query,
            "filters_applied": {"os": os_val, "difficulty": diff_val},
        }
