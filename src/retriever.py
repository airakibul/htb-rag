"""
retriever.py – Hybrid retrieval: BM25 + ChromaDB vector + knowledge graph.

Fuses lexical (BM25Okapi), semantic (Gemini embeddings via ChromaDB),
and structural (NetworkX graph) signals using Reciprocal Rank Fusion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import logging
import re
from typing import Any

from rank_bm25 import BM25Okapi

from src.config import TOP_K
from src.embedder import embed_query, get_all_documents, get_collection
from src.graph_builder import load_graph, query_graph

logger = logging.getLogger(__name__)

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
    "kerberoast": ["kerberoast", "kerberoasting", "getuserspns", "spn", "hashcat 13100"],
    "bloodhound": ["bloodhound", "sharphound", "attack path", "shortest path"],
    "winrm": ["winrm", "evil-winrm", "remote management users"],
    "ms17-010": ["ms17-010", "eternalblue", "cve-2017-0143", "smb-vuln-ms17-010"],
    "eternalblue": ["eternalblue", "ms17-010", "cve-2017-0143", "smb-vuln-ms17-010"],
    "sqlmap": ["sqlmap", "sqli", "sql injection", "--os-shell", "--dump"],
    "docker": ["docker", "docker.sock", "container", "escape", "breakout"],
    "potato": ["potato", "juicypotato", "printspoofer", "seimpersonateprivilege"],
    "printspoofer": ["printspoofer", "seimpersonateprivilege", "spoolss"],
    "juicypotato": ["juicypotato", "seimpersonateprivilege", "clsid"],
    "dcsync": ["dcsync", "secretsdump", "ms-drsr", "getncchanges", "krbtgt", "ntds.dit"],
    "log4j": ["log4j", "log4shell", "cve-2021-44228", "jndi", "ldap"],
    "log4shell": ["log4shell", "log4j", "cve-2021-44228", "jndi", "ldap"],
    "suid": ["suid", "gtfobins", "perm -4000", "setuid"],
    "gtfobins": ["gtfobins", "suid", "perm -4000"],
}


@dataclass
class TechniqueFilter:
    """Declarative technique-specific discriminative filter."""
    trigger_terms: list[str] = field(default_factory=list)      # query must contain ANY of these
    trigger_all: bool = False                                    # if True, query must contain ALL trigger_terms
    trigger_regex: str | None = None                             # regex pattern to match and extract dynamic term
    compound_trigger: list[str] = field(default_factory=list)    # if set, query must also contain at least one of these
    boost_terms: set[str] = field(default_factory=set)           # chunks matching these get boosted
    boost_factor: float = 2.5                                    # score multiplier for matching chunks
    filter_non_matching: bool = True                             # if True, remove chunks that DON'T match boost_terms
    exclude_terms: set[str] = field(default_factory=set)         # chunks with ONLY these (and no boost_terms) are removed
    exclude_os: str | None = None                                # skip chunks with this OS value
    recon_exclusion_terms: set[str] = field(default_factory=set) # pure-recon indicator terms to exclude
    require_any: set[str] = field(default_factory=set)           # chunk must mention at least one of these to survive


TECHNIQUE_FILTERS: list[TechniqueFilter] = [
    # 1. WriteOwner strict discriminative check
    TechniqueFilter(
        trigger_terms=["writeowner"],
        boost_terms={"writeowner", "owneredit", "set-domainobjectowner"},
        boost_factor=2.5,
        filter_non_matching=True,
        exclude_terms={"genericall", "writedacl", "genericwrite"},
    ),
    # 2. Samba RCE strict discriminative check
    TechniqueFilter(
        trigger_terms=["samba"],
        compound_trigger=["rce", "remote code execution", "exploit"],
        boost_terms={
            "cve-2007-2447", "usermap_script", "sambacry", "cve-2017-7494",
            "exploit", "command execution", "remote code", "metasploit", "payload",
        },
        boost_factor=2.5,
        filter_non_matching=True,
        exclude_os="windows",
        require_any={"samba", "smbd", "sambacry"},
        recon_exclusion_terms={
            "smbclient -l", "null session", "enum4linux", "shares listing", "listing shares",
        },
    ),
    # 3. Password Cracking / Hash Dumping check (boost only, keep all chunks)
    TechniqueFilter(
        trigger_terms=["hash dump", "password cracking", "hashcat", "mimikatz", "secretsdump"],
        boost_terms={
            "secretsdump", "mimikatz", "hashcat", "john", "ntds.dit", "sam",
            "as-rep", "kerberoast", "gpp-decrypt",
        },
        boost_factor=1.6,
        filter_non_matching=False,
    ),
    # 4. ESC specific sub-technique check
    TechniqueFilter(
        trigger_regex=r"\b(esc\d+)\b",
        boost_factor=3.0,
        filter_non_matching=True,
    ),
    # 5. MS17-010 / EternalBlue check
    TechniqueFilter(
        trigger_terms=["ms17-010", "eternalblue"],
        boost_terms={"ms17-010", "eternalblue", "cve-2017-0143", "smb-vuln-ms17-010"},
        boost_factor=3.0,
    ),
    # 6. Log4Shell / CVE-2021-44228 check
    TechniqueFilter(
        trigger_terms=["log4j", "log4shell", "cve-2021-44228"],
        boost_terms={"log4j", "log4shell", "cve-2021-44228", "jndi"},
        boost_factor=3.0,
    ),
    # 7. Kerberoasting check
    TechniqueFilter(
        trigger_terms=["kerberoast"],
        boost_terms={"kerberoast", "getuserspns", "spn", "13100"},
        boost_factor=2.5,
    ),
    # 8. sqlmap check
    TechniqueFilter(
        trigger_terms=["sqlmap"],
        boost_terms={"sqlmap", "sqli", "sql injection"},
        boost_factor=2.5,
    ),
    # 9. Docker breakout check
    TechniqueFilter(
        trigger_terms=["docker"],
        compound_trigger=["escape", "breakout"],
        boost_terms={"docker", "docker.sock", "container", "privileged", "cgroup"},
        boost_factor=2.5,
    ),
    # 10. JuicyPotato / PrintSpoofer check
    TechniqueFilter(
        trigger_terms=["juicypotato", "printspoofer", "seimpersonate"],
        boost_terms={"juicypotato", "printspoofer", "seimpersonate", "roguepotato", "sweetpotato"},
        boost_factor=2.5,
    ),
    # 11. DCSync check
    TechniqueFilter(
        trigger_terms=["dcsync"],
        boost_terms={"dcsync", "ds-replication", "getncchanges"},
        boost_factor=2.5,
    ),
    # 12. SUID / GTFOBins check
    TechniqueFilter(
        trigger_terms=["suid", "gtfobins"],
        boost_terms={"suid", "gtfobins", "perm -4000", "setuid"},
        boost_factor=2.5,
    ),
]


def _apply_technique_filters(
    merged: list[dict[str, Any]],
    q_lower: str,
) -> list[dict[str, Any]]:
    """Apply all technique-specific discriminative filters from TECHNIQUE_FILTERS config."""
    for tf in TECHNIQUE_FILTERS:
        dynamic_boost_terms = set(tf.boost_terms)

        # 1. Regex trigger check (e.g. for ESC sub-techniques like esc1, esc8)
        if tf.trigger_regex:
            match = re.search(tf.trigger_regex, q_lower)
            if not match:
                continue
            target_val = match.group(1).lower()
            dynamic_boost_terms.add(target_val)

        # 2. Term trigger check
        elif tf.trigger_terms:
            if tf.trigger_all:
                if not all(t in q_lower for t in tf.trigger_terms):
                    continue
            else:
                if not any(t in q_lower for t in tf.trigger_terms):
                    continue
        else:
            continue

        # 3. Compound trigger check (e.g. docker + escape/breakout, samba + rce/exploit)
        if tf.compound_trigger:
            if not any(w in q_lower for w in tf.compound_trigger):
                continue

        # 4. Filter and boost chunks
        filtered: list[dict[str, Any]] = []
        for c in merged:
            text_str = c.get("text", "")
            bc_str = c.get("metadata", {}).get("breadcrumb", "")
            text_lower = text_str.lower()
            combined_lower = f"{text_lower} {bc_str.lower()}"

            # OS exclusion (e.g. skip Windows chunks for Samba RCE)
            if tf.exclude_os and c.get("metadata", {}).get("os", "").lower() == tf.exclude_os:
                continue

            # Must mention at least one term from require_any
            if tf.require_any and not any(t in combined_lower for t in tf.require_any):
                continue

            has_boost = any(t in combined_lower for t in dynamic_boost_terms)

            # Recon exclusion (e.g. Samba recon commands when looking for RCE)
            if tf.recon_exclusion_terms:
                is_pure_recon = any(recon in text_lower for recon in tf.recon_exclusion_terms) and not has_boost
                if is_pure_recon:
                    continue

            # Boost matching chunks
            if has_boost:
                c["rrf_score"] = c.get("rrf_score", 0.0) * tf.boost_factor
                filtered.append(c)
            elif not tf.filter_non_matching:
                # Boost-only mode: keep all chunks
                filtered.append(c)
            elif tf.exclude_terms:
                # Exclude only if chunk has exclude_terms without having boost_terms
                if not any(term in combined_lower for term in tf.exclude_terms):
                    filtered.append(c)

        if filtered:
            merged = filtered

    return merged


def _compute_lexical_density(query_terms: list[str], text: str, breadcrumb: str) -> float:
    """Compute exact term match density in breadcrumb and text body."""
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
    def detect_query_intent(query: str) -> dict[str, Any]:
        """Lightweight intent extraction from the raw query string."""
        q = query.lower()

        # OS
        windows_signals = [
            "windows", "adcs", "active directory", "bloodhound",
            "shadow credential", "as-rep", "winrm", "genericall",
            "writedacl", "writeowner", "kerberos", "kerberoast", "dcsync", "mimikatz",
            "ms17-010", "eternalblue", "potato", "printspoofer", "juicypotato",
        ]
        if any(sig in q for sig in windows_signals):
            os_val = "windows"
        elif any(sig in q for sig in ["linux", "suid", "gtfobins", "docker"]):
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

        # ── Specific Technique Discriminative Filters (config-driven) ───────
        merged = _apply_technique_filters(merged, q_lower)


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
        rerank_pool = min(len(merged), effective_top_k * 3)
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
