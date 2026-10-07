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
    """Clean, un-overfitted query intent parsing using neural SemanticIntentRouter."""
    from src.infrastructure.intent_router import get_intent_router

    router = get_intent_router()
    intent = router.classify_intent(query)

    query_scope = intent["scope"]
    target_os = intent["target_os"]
    target_phase = intent["target_phase"]

    # Difficulty detection
    low = query.lower()
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
