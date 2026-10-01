"""Backward-compatible shim — delegates to src.pipeline.retriever."""

from src.pipeline.retriever import (  # noqa: F401
    STOPWORDS,
    HybridRetriever,
    _compute_lexical_density,
)

__all__ = ["HybridRetriever", "STOPWORDS", "_compute_lexical_density"]
