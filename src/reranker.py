"""Backward-compatible shim — delegates to src.infrastructure.cross_encoder."""

from src.infrastructure.cross_encoder import (  # noqa: F401
    CrossEncoderReranker,
    _get_model,
    rerank,
)

__all__ = ["CrossEncoderReranker", "_get_model", "rerank"]
