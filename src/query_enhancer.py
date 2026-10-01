"""Backward-compatible shim — delegates to src.pipeline.query_enhancer."""

from __future__ import annotations

from typing import Any
import networkx as nx

from src.domain.models import EnhancedQuery  # noqa: F401
from src.graph.builder import load_graph
from src.graph.querier import query_graph
from src.pipeline.query_enhancer import (
    _fallback_enhance as _pipeline_fallback_enhance,
)


def _fallback_enhance(query: str, graph: nx.DiGraph | None = None) -> EnhancedQuery:
    g = graph if graph is not None else load_graph()
    return _pipeline_fallback_enhance(query, g)


def enhance_query(query: str, graph: nx.DiGraph | None = None) -> EnhancedQuery:
    return _fallback_enhance(query, graph)


__all__ = [
    "EnhancedQuery",
    "_fallback_enhance",
    "enhance_query",
    "load_graph",
    "query_graph",
]
