"""
reranker.py – Cross-encoder re-ranking for improved retrieval precision.

Uses a lightweight cross-encoder model to rescore (query, chunk) pairs
with full bidirectional attention after initial BM25 + vector retrieval.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_cross_encoder = None


def _get_model():
    """Load the cross-encoder model (loads locally in < 0.3s without remote network ping)."""
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            try:
                _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", local_files_only=True)
            except Exception:
                _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Cross-encoder model loaded: ms-marco-MiniLM-L-6-v2")
        except Exception as exc:
            logger.warning(f"Cross-encoder unavailable, skipping re-rank: {exc}")
            _cross_encoder = False  # sentinel: don't retry
    return _cross_encoder


def rerank(
    query: str,
    chunks: list[dict[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Re-rank chunks using cross-encoder scores.

    Falls back gracefully to the original ordering if the model
    is unavailable or any error occurs.

    Parameters
    ----------
    query : str
        The user's query string.
    chunks : list[dict]
        Chunk dicts with at least a ``"text"`` key.
    top_k : int | None
        If set, return only the top_k re-ranked results.

    Returns
    -------
    list[dict]
        Chunks sorted by cross-encoder score (descending), each with
        an added ``"ce_score"`` field.
    """
    model = _get_model()
    if not model or not chunks:
        return chunks[:top_k] if top_k else chunks

    try:
        # Build (query, document) pairs — truncate document to ~512 chars
        # to stay within the model's token limit
        pairs = [(query, c.get("text", "")[:512]) for c in chunks]

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
