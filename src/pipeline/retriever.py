"""
retriever.py – Hybrid retrieval: BM25 + VectorStore + GraphStore + Cross-Encoder Reranker.

Follows SOLID Principles (SRP, OCP, DIP) and Clean Architecture:
- Single Responsibility: Extracted BM25SearchIndex, RankFusionEngine, and ResultDiversifier.
- Dependency Inversion: Depends on Domain interfaces (VectorStore, GraphStore, etc.)
  with lazy fallback adapter creation, eliminating tight module-level coupling.
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
    IntentClassifier,
    Reranker,
    VectorStore,
)
from src.domain.models import RetrievalResult
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
    combined = f"{breadcrumb} {breadcrumb} {text}".lower()
    matches = sum(1 for term in query_terms if term in combined)
    return matches / max(len(query_terms), 1)


# ── Lazy Dependency Inversion Helpers ─────────────────────────────────────────

def _default_vector_store() -> VectorStore:
    from src.infrastructure.chroma_store import ChromaStore
    return ChromaStore()


def _default_graph_store() -> GraphStore:
    from src.infrastructure.networkx_graph import NetworkXGraphStore
    return NetworkXGraphStore()


def _default_embedding_service() -> EmbeddingService:
    from src.infrastructure.sentence_transformer import SentenceTransformerEmbeddingService
    return SentenceTransformerEmbeddingService()


def _default_reranker() -> Reranker:
    from src.infrastructure.cross_encoder import CrossEncoderReranker
    return CrossEncoderReranker()


# ═════════════════════════════════════════════════════════════════════════════
#  SRP Component: BM25 Lexical Index
# ═════════════════════════════════════════════════════════════════════════════

class BM25SearchIndex:
    """Encapsulates BM25 corpus preparation, cyber-aware tokenization, and lexical search."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs
        corpus = [self.tokenize(doc["text"]) for doc in docs]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Cyber-aware tokenization: preserves compound identifiers while indexing sub-tokens."""
        tokens: list[str] = []
        raw_words = text.lower().split()
        for w in raw_words:
            clean = w.strip("?,.!\"':;()[]{}<>`~*")
            if not clean:
                continue
            tokens.append(clean)
            if any(delim in clean for delim in ("-", "_", ".", "/", "\\", ":")):
                sub_parts = re.split(r"[-_./\\:]+", clean)
                for part in sub_parts:
                    if len(part) > 1 and part != clean:
                        tokens.append(part)
        return tokens

    def get_scores_for_query(self, query: str) -> Any:
        """Return raw BM25 scores across all corpus documents for a query."""
        if not self.bm25 or not self.docs:
            return []
        words = self.tokenize(query)
        clean_tokens = [w for w in words if w not in STOPWORDS]
        tokens = clean_tokens if clean_tokens else words
        if not tokens:
            tokens = query.lower().split()
        return self.bm25.get_scores(tokens)

    def search(
        self, query: str, top_k: int = TOP_K, os_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Return the top_k BM25 hits, respecting OS filter if specified."""
        if not self.bm25 or not self.docs:
            return []

        scores = self.get_scores_for_query(query)

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


# ═════════════════════════════════════════════════════════════════════════════
#  SRP Component: Reciprocal Rank Fusion Engine
# ═════════════════════════════════════════════════════════════════════════════

class RankFusionEngine:
    """Multi-channel rank fusion engine implementing Reciprocal Rank Fusion (RRF)."""

    @staticmethod
    def fuse(
        bm25_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        k: int = 60,
        extra_results: list[list[dict[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        """Merge ranked lists using principled multi-channel RRF."""
        scores: dict[str, float] = {}
        doc_map: dict[str, dict[str, Any]] = {}

        all_lists = [bm25_results, vector_results]
        if extra_results:
            all_lists.extend(extra_results)

        for result_list in all_lists:
            for item in result_list:
                key = hashlib.md5(item["text"].encode("utf-8")).hexdigest()
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + item["rank"])

                if key not in doc_map:
                    doc_map[key] = item

        ranked_keys = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]

        merged: list[dict[str, Any]] = []
        for rank, key in enumerate(ranked_keys, 1):
            entry = dict(doc_map[key])
            entry["rrf_score"] = scores[key]
            entry["rank"] = rank
            merged.append(entry)

        return merged


# ═════════════════════════════════════════════════════════════════════════════
#  SRP Component: Result Diversifier
# ═════════════════════════════════════════════════════════════════════════════

class ResultDiversifier:
    """Enforces target-aware source diversity across retrieved chunks without artificial gating."""

    @staticmethod
    def diversify(
        chunks: list[dict[str, Any]],
        query: str,
        is_broad: bool = False,
        effective_top_k: int = 8,
        max_per_machine: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Diversify chunks to avoid single verbose writeups flooding context."""
        targets_specific_machine = bool(re.search(r"\bhtb-[a-z0-9_-]+\b", query.lower()))
        if max_per_machine is not None:
            per_machine_cap = max_per_machine
        elif targets_specific_machine:
            per_machine_cap = effective_top_k
        elif is_broad:
            per_machine_cap = 1
        else:
            per_machine_cap = 2

        diversified: list[dict[str, Any]] = []
        machine_counts: dict[str, int] = {}

        # Pure neural ranking: retain the cross-encoder's relevance order
        for chunk in chunks:
            src = chunk.get("metadata", {}).get("source", "unknown").lower()
            count = machine_counts.get(src, 0)
            if count < per_machine_cap:
                diversified.append(chunk)
                machine_counts[src] = count + 1

            if len(diversified) >= effective_top_k:
                break

        for rank, chunk in enumerate(diversified, 1):
            chunk["rank"] = rank

        return diversified


# ═════════════════════════════════════════════════════════════════════════════
#  Hybrid Retriever (Orchestrator)
# ═════════════════════════════════════════════════════════════════════════════

class HybridRetriever:
    """Three-signal retriever with reciprocal-rank fusion and interface-based DI."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        graph_store: GraphStore | None = None,
        embedding_service: EmbeddingService | None = None,
        reranker: Reranker | None = None,
        intent_classifier: IntentClassifier | None = None,
    ) -> None:
        self.vector_store: VectorStore = vector_store or _default_vector_store()
        self.graph_store: GraphStore = graph_store or _default_graph_store()
        self.embedding_service: EmbeddingService = (
            embedding_service or _default_embedding_service()
        )
        self.reranker: Reranker = reranker or _default_reranker()
        self.intent_classifier: IntentClassifier | None = intent_classifier

        # Load every document from VectorStore
        self.docs: list[dict[str, Any]] = self.vector_store.get_all_documents()

        # Dedicated BM25 index component (SRP)
        self._bm25_index = BM25SearchIndex(self.docs)
        self.bm25 = self._bm25_index.bm25

        # Expose graph & collection for backward-compatibility
        self.graph = getattr(self.graph_store, "graph", None)
        self.collection = getattr(self.vector_store, "collection", None)

        # Inverted index of source machine -> document chunks and indices for graph-guided candidate retrieval
        self._machine_docs: dict[str, list[dict[str, Any]]] = {}
        self._machine_doc_indices: dict[str, list[int]] = {}
        for idx, doc in enumerate(self.docs):
            src = doc.get("metadata", {}).get("source", "").lower()
            if src:
                self._machine_docs.setdefault(src, []).append(doc)
                self._machine_doc_indices.setdefault(src, []).append(idx)

        stats = (
            self.graph_store.get_stats()
            if hasattr(self.graph_store, "get_stats")
            else {}
        )
        n_nodes = stats.get("nodes", self.graph.number_of_nodes() if self.graph is not None else 0)
        logger.info(
            f"🔎 HybridRetriever ready  "
            f"({len(self.docs)} docs, {n_nodes} graph nodes)"
        )

    # ── BM25 Delegator ──────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return BM25SearchIndex.tokenize(text)

    def bm25_search(
        self, query: str, top_k: int = TOP_K, os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._bm25_index.search(query, top_k=top_k, os_filter=os_filter)

    # ── Vector Search ────────────────────────────────────────────────────

    def vector_search(
        self,
        query: str,
        top_k: int = TOP_K,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the top_k nearest-neighbour hits from VectorStore."""
        q_embedding = self.embedding_service.embed_query(query)
        return self.vector_store.query(embedding=q_embedding, top_k=top_k, where=where)

    # ── Rank Fusion Delegator ────────────────────────────────────────────

    @staticmethod
    def reciprocal_rank_fusion(
        bm25_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
        k: int = 60,
        extra_results: list[list[dict[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        return RankFusionEngine.fuse(
            bm25_results, vector_results, k=k, extra_results=extra_results
        )

    # ── Metadata filter builder ──────────────────────────────────────────

    @staticmethod
    def build_where_filter(
        os: str | None = None,
        difficulty: str | None = None,
    ) -> dict[str, Any] | None:
        """Build a ChromaDB-compatible ``$and`` filter from optional params."""
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
    def detect_query_intent(
        query: str,
        graph: Any = None,
        router: IntentClassifier | None = None,
    ) -> dict[str, Any]:
        """Dynamically extract query intent using enhance_query (LLM + Knowledge Graph)."""
        enh = enhance_query(query, graph, router=router)
        return {
            "os": enh.target_os,
            "difficulty": enh.difficulty,
            "query_type": "structured" if enh.query_scope == "broad" else "semantic",
            "phase": enh.target_phase,
            "scope": enh.query_scope,
            "expanded_terms": enh.expanded_terms,
            "expanded_query": enh.expanded_query,
            "multi_queries": enh.multi_queries,
            "suggested_top_k": enh.suggested_top_k,
        }

    # ── Main retrieve entry-point ────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K,
        os_filter: str | None = None,
        difficulty_filter: str | None = None,
    ) -> RetrievalResult:
        """Run the full hybrid retrieval pipeline."""
        # Dynamic intent detection and query expansion
        router = getattr(self, "intent_classifier", None)
        intent = self.detect_query_intent(query, self.graph, router=router)

        os_val   = os_filter   or intent["os"]
        diff_val = difficulty_filter or intent["difficulty"]

        where = self.build_where_filter(os_val, diff_val)

        graph_hits = self.graph_store.query_graph(query)
        n_graph_machines = len(graph_hits.get("relevant_machines", [])) if graph_hits else 0

        # Scope-based settings with LLM-adaptive budget & graph fallback
        scope = intent.get("scope", "specific")
        is_broad = (scope == "broad")
        llm_suggested_k = intent.get("suggested_top_k")

        base_k = top_k or TOP_K or 6
        if is_broad:
            candidate_pool = 25  # Lean candidate pool: fast CPU cross-encoder reranking (~2s)
            # Lean & high-precision budget: 6-8 chunks for detailed steps, letting Graph Manifest provide corpus inventory
            if llm_suggested_k and isinstance(llm_suggested_k, int):
                effective_top_k = min(max(llm_suggested_k, 5), 8)
            else:
                effective_top_k = min(max(base_k, 6), 8)
            max_per_machine = 1
        else:
            candidate_pool = 20  # Fast CPU candidate pool (~1.5s)
            # For specific query: 4-6 pinpoint chunks
            if llm_suggested_k and isinstance(llm_suggested_k, int):
                effective_top_k = min(max(llm_suggested_k, 4), 6)
            else:
                effective_top_k = min(base_k, 5) if base_k else 5
            max_per_machine = 2

        # Stage 1: Candidate Generation (BM25 Lexical + Dense Vector Semantic)
        bm25_hits = self.bm25_search(query, top_k=candidate_pool, os_filter=os_val)
        vector_hits = self.vector_search(query, top_k=candidate_pool, where=where)

        # Phase 4: Multi-Query Retrieval (LLM Sub-queries + Graph Techniques)
        extra_channels: list[list[dict[str, Any]]] = []
        extra_queries: list[str] = []
        for sq in intent.get("multi_queries", []):
            if sq and sq.lower().strip() != query.lower().strip() and sq not in extra_queries:
                extra_queries.append(sq)

        if graph_hits:
            matched_techs = [
                t for t in graph_hits.get("matched_techniques", [])
                if isinstance(t, str) and t.strip()
            ][:3]
            for t in matched_techs:
                if t not in extra_queries:
                    extra_queries.append(t)

        for eq in extra_queries[:3]:  # Cap at top 3 extra query angles to bound latency
            eq_bm25 = self.bm25_search(eq, top_k=25, os_filter=os_val)
            eq_vec = self.vector_search(eq, top_k=25, where=where)
            if eq_bm25:
                extra_channels.append(eq_bm25)
            if eq_vec:
                extra_channels.append(eq_vec)

        # Multi-Channel Reciprocal Rank Fusion (unbiased fusion of lexical + semantic ranks)
        merged = self.reciprocal_rank_fusion(
            bm25_hits,
            vector_hits,
            k=60,
            extra_results=extra_channels if extra_channels else None,
        )
        merged.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

        # Stage 1.5: Graph-Guided Candidate Injection (Phase 1: Broad Query Coverage Expansion)
        # Pull best chunk per missing graph-connected machine so the cross-encoder can evaluate them
        if graph_hits and (is_broad or graph_hits.get("matched_techniques") or graph_hits.get("matched_cves")):
            graph_machines = graph_hits.get("relevant_machines", [])
            machine_docs = getattr(self, "_machine_docs", {})
            if graph_machines and machine_docs:
                already_retrieved = {
                    c.get("metadata", {}).get("source", "").lower()
                    for c in merged
                    if c.get("metadata", {}).get("source")
                }
                missing_machines = [
                    m for m in graph_machines
                    if m.lower() not in already_retrieved and m.lower() in machine_docs
                ][:30]  # Cap at 25-30 extra candidates to prevent pool bloat

                if missing_machines:
                    bm25_index = getattr(self, "_bm25_index", None)
                    bm25_scores = (
                        bm25_index.get_scores_for_query(query)
                        if bm25_index is not None
                        else None
                    )
                    machine_indices = getattr(self, "_machine_doc_indices", {})
                    injected_chunks: list[dict[str, Any]] = []

                    for rank_offset, m in enumerate(missing_machines, 1):
                        m_low = m.lower()
                        indices = machine_indices.get(m_low, [])
                        if not indices and m_low in machine_docs:
                            doc_list = machine_docs[m_low]
                            if doc_list:
                                injected_chunks.append({
                                    "text": doc_list[0].get("text", ""),
                                    "metadata": doc_list[0].get("metadata", {}),
                                    "score": 0.0,
                                    "rrf_score": 0.0,
                                    "rank": len(merged) + rank_offset,
                                    "source_channel": "graph_expansion",
                                })
                            continue

                        # Respect OS filter if active
                        if os_val:
                            filtered_indices = [
                                i for i in indices
                                if self.docs[i].get("metadata", {}).get("os", "unknown") in (os_val, "unknown")
                            ]
                            if filtered_indices:
                                indices = filtered_indices

                        if not indices:
                            continue

                        if bm25_scores is not None and len(bm25_scores) > 0:
                            best_idx = max(indices, key=lambda i: bm25_scores[i])
                            best_score = float(bm25_scores[best_idx])
                        else:
                            best_idx = indices[0]
                            best_score = 0.0

                        best_doc = self.docs[best_idx]
                        injected_chunks.append({
                            "text": best_doc.get("text", ""),
                            "metadata": best_doc.get("metadata", {}),
                            "score": best_score,
                            "rrf_score": 0.0,
                            "rank": len(merged) + rank_offset,
                            "source_channel": "graph_expansion",
                        })

                    if injected_chunks:
                        # Append with lower initial rank so they don't displace top RRF hits,
                        # but guarantee they fit within the cross-encoder rerank pool
                        target_pool_budget = 120
                        base_budget = max(0, target_pool_budget - len(injected_chunks))
                        merged = merged[:base_budget] + injected_chunks

        # Stage 2: Cross-Encoder Re-Ranking on candidate pool (fast reranking on 40-60 items)
        rerank_pool = min(len(merged), 60 if is_broad else 40)
        merged[:rerank_pool] = self.reranker.rerank(query, merged[:rerank_pool])

        # Stage 3: Source Diversification (pure neural cross-encoder order, no artificial cut-offs)
        final_chunks = ResultDiversifier.diversify(
            merged,
            query=query,
            is_broad=is_broad,
            effective_top_k=effective_top_k,
            max_per_machine=max_per_machine,
        )

        # Stage 4: Knowledge Graph Manifest Injection for Broad Queries (Corpus-Wide Coverage)
        manifest = None
        if is_broad:
            manifest = self.graph_store.get_manifest_for_query(query, os_filter=os_val)
            if manifest:
                logger.info(f"📋 Graph Manifest attached: {len(manifest)} machines for corpus coverage")

        return RetrievalResult(
            chunks=final_chunks[:effective_top_k],
            graph_hits=graph_hits,
            query=query,
            filters_applied={"os": os_val, "difficulty": diff_val},
            manifest=manifest,
        )
