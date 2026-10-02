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

    # Scope detection: broad cheatsheet/catalog vs specific technique/exploit
    has_broad_intent = any(
        w in low for w in ["cheatsheet", "cheat sheet", "overview", "attack techniques", "techniques across"]
    )
    has_cve = bool(re.search(r"cve-\d{4}-\d+", low)) or bool(re.search(r"\bms\d{2}-\d{3}\b", low))
    has_specific_how = any(p in low for p in ["how does", "how is", "how was", "which htb", "which machines"])

    if has_broad_intent and not has_cve and not has_specific_how:
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
