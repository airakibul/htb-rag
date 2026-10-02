"""
models.py – Domain models for HTB RAG pipeline.

Pure business data representations with no I/O dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A single retrieved text chunk with metadata."""
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    rank: int = 0
    rrf_score: float = 0.0
    ce_score: float | None = None


@dataclass
class RetrievalResult:
    """Complete output from the retrieval pipeline."""
    chunks: list[dict[str, Any]] | list[Chunk]
    graph_hits: dict[str, Any] = field(default_factory=dict)
    query: str = ""
    filters_applied: dict[str, Any] = field(default_factory=dict)
    manifest: list[dict[str, Any]] | None = None  # NEW: for Week 2

    def __getitem__(self, key: str) -> Any:
        if key == "graph":
            return self.graph_hits
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "graph":
            return self.graph_hits
        if hasattr(self, key):
            val = getattr(self, key)
            return val if val is not None else default
        return default

    def __contains__(self, key: str) -> bool:
        return key in ("chunks", "graph_hits", "graph", "query", "filters_applied", "manifest")

    def keys(self) -> list[str]:
        return ["chunks", "graph", "graph_hits", "query", "filters_applied", "manifest"]

    def items(self) -> list[tuple[str, Any]]:
        return [(k, self.get(k)) for k in self.keys()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunks": self.chunks,
            "graph": self.graph_hits,
            "graph_hits": self.graph_hits,
            "query": self.query,
            "filters_applied": self.filters_applied,
            "manifest": self.manifest,
        }


@dataclass
class SynthesisResult:
    """Output from the LLM synthesis step."""
    answer: str
    sources: list[str] = field(default_factory=list)
    chunks_used: int = 0
    graph_used: bool = False
    provider: str = "none"


@dataclass
class EnhancedQuery:
    """Encapsulates dynamically parsed query signals."""
    query: str
    expanded_query: str
    expanded_terms: list[str] = field(default_factory=list)
    target_os: str | None = None
    query_scope: str = "specific"
    target_phase: str | None = None
    difficulty: str | None = None
    multi_queries: list[str] = field(default_factory=list)


@dataclass
class QueryIntent:
    """Encapsulates detected query intent signals."""
    os: str | None = None
    difficulty: str | None = None
    query_type: str = "semantic"
    phase: str | None = None
    scope: str = "specific"
    expanded_terms: list[str] = field(default_factory=list)
    expanded_query: str = ""
    multi_queries: list[str] = field(default_factory=list)

