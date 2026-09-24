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

STOPWORDS: set[str] = {
    "what", "are", "the", "common", "across", "machines", "machine",
    "htb", "provide", "a", "an", "which", "demonstrate", "demonstrates",
    "how", "was", "it", "exploited", "each", "one", "and", "used", "is",
    "for", "in", "of", "to", "with", "show", "techniques", "cheatsheet",
    "give", "seen",
}

QUERY_EXPANSIONS: dict[str, list[str]] = {
    "samba": ["samba", "smbd", "cve-2007-2447", "usermap_script", "sambacry", "cve-2017-7494"],
    "adcs": ["adcs", "certipy", "esc1", "esc8", "esc9", "certificate", "templates"],
    "shadow credential": ["shadow credential", "certipy", "pywhisker", "whisker", "msds-keycredentiallink"],
    "genericall": ["genericall", "powerview", "bloodyad", "net rpc password", "dacledit"],
    "writeowner": ["writeowner", "set-domainobjectowner", "powerview", "owneredit"],
    "as-rep": ["as-rep", "roasting", "getnpusers", "dont_req_preauth", "hashcat 18200"],
    "bloodhound": ["bloodhound", "sharphound", "attack path", "shortest path"],
    "winrm": ["winrm", "evil-winrm", "5985", "remote management users"],
}



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
        windows_signals = [
            "windows", "adcs", "active directory", "bloodhound",
            "shadow credential", "as-rep", "winrm", "genericall",
            "writedacl", "writeowner", "kerberos", "dcsync", "mimikatz",
        ]
        if any(sig in q for sig in windows_signals):
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

        # Attack phase signal
        phase_val = None
        if any(w in q for w in ["privilege escalation", "privesc", "root", "administrator", "system hive", "potato", "watson"]):
            phase_val = "privesc"

        return {
            "os": os_val,
            "difficulty": diff_val,
            "query_type": query_type,
            "phase": phase_val,
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

        # Apply query expansion
        q_lower = query.lower()
        expanded_query = query
        for k, terms in QUERY_EXPANSIONS.items():
            if k in q_lower:
                expanded_query += " " + " ".join(terms)

        # ── Adaptive Top-K and Candidate Pool based on Query Intent ─────────
        is_specific = bool(re.search(r"cve-\d{4}-\d+", q_lower)) or any(w in q_lower for w in ["cve", "esc9", "which machine", "how was", "step by step"])
        is_broad = any(w in q_lower for w in ["cheatsheet", "common", "across"]) and not is_specific

        if is_broad:
            effective_top_k = max(top_k, 15)   # Expand to 15 unique machines for cheatsheets
            candidate_pool = max(effective_top_k * 5, 80)
        else:
            effective_top_k = min(top_k, 5)    # Strict small window for specific queries
            candidate_pool = 25

        # Three retrieval channels
        bm25_hits   = self.bm25_search(expanded_query, top_k=candidate_pool, os_filter=os_val)
        vector_hits = self.vector_search(expanded_query, top_k=candidate_pool, where=where)
        graph_hits  = query_graph(self.graph, query)

        # Fuse BM25 + vector
        merged = self.reciprocal_rank_fusion(bm25_hits, vector_hits, k=60)

        # Phase Boost: if user asks for privesc, boost chunks with attack_phase == 'privesc'
        if intent.get("phase") == "privesc":
            for chunk in merged:
                if chunk.get("metadata", {}).get("attack_phase") == "privesc":
                    chunk["rrf_score"] = chunk.get("rrf_score", 0.0) * 1.4

        # Specific CVE Boost: exact match in cve_ids gets 5x score
        cve_match = re.search(r"cve-\d{4}-\d+", q_lower)
        if cve_match:
            target_cve = cve_match.group(0).upper()
            for chunk in merged:
                chunk_cves = str(chunk.get("metadata", {}).get("cve_ids", ""))
                if target_cve in chunk_cves.upper():
                    chunk["rrf_score"] = chunk.get("rrf_score", 0.0) * 5.0

        # Graph Boost: apply 1.5x score boost to chunks whose source is in graph_hits["relevant_machines"]
        relevant_machines = set(graph_hits.get("relevant_machines", []))
        if relevant_machines:
            for chunk in merged:
                src = chunk.get("metadata", {}).get("source", "")
                if src in relevant_machines:
                    chunk["rrf_score"] = chunk.get("rrf_score", 0.0) * 1.5

        # ── Specific Technique Discriminative Filters ───────────────────────
        # 1. WriteOwner strict discriminative check
        if "writeowner" in q_lower:
            writeowner_terms = {"writeowner", "owneredit", "set-domainobjectowner"}
            filtered_merged = []
            for c in merged:
                text_lower = (c.get("text", "") + " " + c.get("metadata", {}).get("breadcrumb", "")).lower()
                # Strongly penalize chunks that only talk about GenericAll/WriteDACL without mentioning owner
                if any(term in text_lower for term in writeowner_terms):
                    c["rrf_score"] = c.get("rrf_score", 0.0) * 2.5
                    filtered_merged.append(c)
                elif not any(term in text_lower for term in ["genericall", "writedacl", "genericwrite"]):
                    filtered_merged.append(c)
            if filtered_merged:
                merged = filtered_merged

        # 2. Samba RCE strict discriminative check
        if "samba" in q_lower and any(w in q_lower for w in ["rce", "remote code execution", "exploit"]):
            samba_rce_terms = {"cve-2007-2447", "usermap_script", "sambacry", "cve-2017-7494", "exploit", "command execution", "remote code", "metasploit", "payload"}
            recon_indicators = {"smbclient -l", "null session", "enum4linux", "shares listing", "listing shares"}
            filtered_merged = []
            for c in merged:
                text_lower = c.get("text", "").lower()
                bc_lower = c.get("metadata", {}).get("breadcrumb", "").lower()
                has_rce = any(term in text_lower for term in samba_rce_terms) or any(term in bc_lower for term in samba_rce_terms)
                is_pure_recon = any(recon in text_lower for recon in recon_indicators) and not has_rce
                if has_rce and not is_pure_recon:
                    c["rrf_score"] = c.get("rrf_score", 0.0) * 2.5
                    filtered_merged.append(c)
                elif not is_pure_recon:
                    filtered_merged.append(c)
            if filtered_merged:
                merged = filtered_merged

        # 3. Password Cracking / Hash Dumping check
        if any(w in q_lower for w in ["hash dump", "password cracking", "hashcat", "mimikatz", "secretsdump"]):
            hash_terms = {"secretsdump", "mimikatz", "hashcat", "john", "ntds.dit", "sam", "as-rep", "kerberoast", "gpp-decrypt"}
            for c in merged:
                text_lower = c.get("text", "").lower()
                if any(term in text_lower for term in hash_terms):
                    c["rrf_score"] = c.get("rrf_score", 0.0) * 1.6

        merged.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

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

        # Specific Query Cutoff: if top chunk has high confidence, drop weak tail
        final_chunks = diversified
        if not is_broad and len(final_chunks) > 1:
            top_score = final_chunks[0].get("rrf_score", 0.0)
            final_chunks = [c for c in final_chunks if c.get("rrf_score", 0.0) >= top_score * 0.60][:effective_top_k]

        return {
            "chunks":          final_chunks[:effective_top_k],
            "graph":           graph_hits,
            "query":           query,
            "filters_applied": {"os": os_val, "difficulty": diff_val},
        }
