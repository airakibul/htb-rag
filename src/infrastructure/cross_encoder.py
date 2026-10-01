"""
cross_encoder.py – Cross-encoder re-ranking implementation.

Concrete adapter implementing the domain Reranker interface using
ms-marco-MiniLM-L-6-v2 cross-encoder.
"""

from __future__ import annotations

import logging
from typing import Any

from src.domain.interfaces import Reranker

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_cross_encoder: Any = None


def _get_model(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> Any:
    """Load the cross-encoder model (loads locally in < 0.3s without remote network ping)."""
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            try:
                _cross_encoder = CrossEncoder(model_name, local_files_only=True)
            except Exception:
                _cross_encoder = CrossEncoder(model_name)
            logger.info(f"Cross-encoder model loaded: {model_name}")
        except Exception as exc:
            logger.warning(f"Cross-encoder unavailable, skipping re-rank: {exc}")
            _cross_encoder = False  # sentinel: don't retry
    return _cross_encoder


def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    top_k: int | None = None,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> list[dict[str, Any]]:
    """Re-rank chunks using cross-encoder scores.

    Falls back gracefully to the original ordering if the model
    is unavailable or any error occurs.
    """
    model = _get_model(model_name)
    if not model or not chunks:
        return chunks[:top_k] if top_k else chunks

    try:
        # Build (query, document) pairs — truncate document to ~1800 chars
        # (~450 tokens), safely within the ms-marco 512-token limit
        pairs = [(query, c.get("text", "")[:1800]) for c in chunks]

        scores = model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk["ce_score"] = float(score)

        # Sort descending by cross-encoder score
        chunks.sort(key=lambda x: x.get("ce_score", 0.0), reverse=True)

        if top_k:
            chunks = chunks[:top_k]

        # Re-assign rank
        for i, chunk in enumerate(chunks, 1):
            chunk["rank"] = i

        return chunks

    except Exception as exc:
        logger.warning(f"Cross-encoder re-rank failed, returning original order: {exc}")
        return chunks[:top_k] if top_k else chunks


class CrossEncoderReranker(Reranker):
    """Reranker implementation using ms-marco cross-encoder."""

    def __init__(
        self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ) -> None:
        self.model_name = model_name

    def rerank(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        return rerank(query=query, chunks=chunks, top_k=top_k, model_name=self.model_name)
