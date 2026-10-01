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
    chunks: list[Chunk]
    graph_hits: dict[str, Any] = field(default_factory=dict)
    query: str = ""
    filters_applied: dict[str, Any] = field(default_factory=dict)
    manifest: list[dict[str, Any]] | None = None  # NEW: for Week 2


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
