"""
query_enhancer.py – Lightweight, non-overfitting query analysis and metadata extraction.

Performs pure query intent parsing (scope, OS, phase) without modifying or keyword-stuffing
the user's authentic search query.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import networkx as nx

from src.domain.models import EnhancedQuery
from src.graph.builder import load_graph
from src.graph.querier import query_graph

logger = logging.getLogger(__name__)


def _fallback_enhance(query: str, graph: nx.DiGraph | None = None) -> EnhancedQuery:
    """Clean, un-overfitted query intent parsing."""
    low = query.lower()

    # 1. Definite Specific Anchors (Exact vulnerability / exploit identifiers)
    has_cve = bool(re.search(r"\bcve-\d{4}-\d+\b", low)) or bool(re.search(r"\bms\d{2}-\d{3}\b", low))
    if has_cve:
        query_scope = "specific"
    else:
        # 2. Definite Specific Procedural Anchors (How does a single mechanism/tool work)
        is_procedural = bool(re.search(r"\bhow\s+(?:does|is|was|were|to)\b", low))
        is_definition = bool(re.search(r"\bwhat\s+is\s+[a-z0-9\-]+\s*\([^\)]+\)", low))

        if is_procedural or is_definition:
            query_scope = "specific"
        else:
            # 3. Broad Semantic Indicators (Cheatsheet / Catalog / Domain Collection)
            has_cs = bool(re.search(r"\b(?:cheat\s*sheet|overview|catalog|handbook)\b", low))
            has_tech_domain = bool(re.search(
                r"\b(?:attack|abuse|privesc|privilege\s+escalation|cracking|dumping|injection|recon(?:naissance)?|lateral\s+movement)\s+(?:techniques|vulnerabilities|methods|vectors|attacks)\b",
                low,
            ))
            plural_entities = bool(re.search(r"\b(?:techniques|vulnerabilities|attacks|methods|vectors|exploits|flaws)\b", low))
            cross_corpus = bool(re.search(r"\b(?:across|common|all\s+machines|various|different|types\s+of|list\s+of|shown\s+across|used\s+across|seen\s+across)\b", low))

            if has_cs or has_tech_domain or (plural_entities and cross_corpus):
                query_scope = "broad"
            else:
                query_scope = "specific"

    # Explicit phase detection
    target_phase = None
    if "privilege escalation" in low or "privesc" in low:
        target_phase = "privesc"
    elif any(w in low for w in ["foothold", "initial access", "rce", "remote code execution"]):
        target_phase = "foothold"
    elif any(w in low for w in ["recon", "enumeration", "port scan"]):
        target_phase = "recon"

    # OS detection
    target_os = None
    linux_indicators = ["linux", "suid", "gtfobins", "linpeas"]
    windows_indicators = ["windows", "adcs", "kerberos", "active directory", "winpeas"]
    has_linux = any(w in low for w in linux_indicators)
    has_windows = any(w in low for w in windows_indicators)
    if has_windows and not has_linux:
        target_os = "windows"
    elif has_linux and not has_windows:
        target_os = "linux"

    # Difficulty detection
    difficulty = None
    for d in ("insane", "hard", "medium", "easy"):
        if re.search(rf"\b{d}\b", low):
            difficulty = d
            break

    # Standard CVE aliases from graph if a CVE is explicitly queried
    expanded_terms: list[str] = []
    cve_matches = re.findall(r"cve-\d{4}-\d+", low)
    if cve_matches:
        g = graph if graph is not None else load_graph()
        if g is not None:
            for cve in cve_matches:
                cve_upper = cve.upper()
                if cve_upper in g:
                    expanded_terms.extend(g.nodes[cve_upper].get("aliases", []))

    # Keep query untouched — NO artificial keyword stuffing or appending
    return EnhancedQuery(
        query=query,
        expanded_query=query,
        expanded_terms=expanded_terms,
        target_os=target_os,
        query_scope=query_scope,
        target_phase=target_phase,
        difficulty=difficulty,
        multi_queries=[query],
    )


def generate_multi_queries(query: str, enh: EnhancedQuery | None = None) -> list[str]:
    """Return authentic query list without artificial prompt mutations."""
    if enh is not None and enh.multi_queries:
        return enh.multi_queries
    return [query]


def enhance_query(query: str, graph: nx.DiGraph | None = None) -> EnhancedQuery:
    """Enhance user query dynamically without query mutation."""
    return _fallback_enhance(query, graph)
