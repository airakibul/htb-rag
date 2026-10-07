"""
sentence_transformer.py – SentenceTransformer embedding service implementation.

Concrete adapter implementing the domain EmbeddingService interface.
Uses local SentenceTransformer embeddings with zero rate limits and a
deterministic hash-based fallback.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import numpy as np

from src.config import EMBEDDING_MODEL_NAME
from src.domain.interfaces import EmbeddingService

logger = logging.getLogger(__name__)

# Lazy-loaded SentenceTransformer embedding model singleton
_embed_model: Any = None


def _get_embed_model(model_name: str = EMBEDDING_MODEL_NAME) -> Any:
    """Lazy-load the local SentenceTransformer embedding model."""
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
            logger.info(f"Loading local SentenceTransformer model: {model_name}...")
            try:
                _embed_model = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                _embed_model = SentenceTransformer(model_name)
            # Increase sequence length from 256 to 512 to prevent semantic truncation underfitting on ~2400 char chunks
            if hasattr(_embed_model, "max_seq_length") and _embed_model.max_seq_length < 512:
                _embed_model.max_seq_length = 512
            logger.info(f"✅ Loaded SentenceTransformer model: {model_name} (max_seq_length={getattr(_embed_model, 'max_seq_length', 512)})")
        except Exception as exc:
            logger.error(f"❌ Failed to load SentenceTransformer: {exc}")
            raise
    return _embed_model


def _local_hash_embedding(text: str, dim: int = 384) -> list[float]:
    """Deterministic 384-dim feature hash vectorizer fallback."""
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return [0.0] * dim
    vec = np.zeros(dim, dtype=np.float32)
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % dim
        val = 1.0 if (h & 1) else -1.0
        vec[idx] += val
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()


class SentenceTransformerEmbeddingService(EmbeddingService):
    """EmbeddingService implementation backed by SentenceTransformer."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME) -> None:
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple texts using local SentenceTransformer with zero rate limits."""
        if not texts:
            return []
        try:
            model = _get_embed_model(self.model_name)
            embeddings = model.encode(
                texts,
                batch_size=min(len(texts), 128),
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return embeddings.tolist()
        except Exception as exc:
            logger.warning(
                f"SentenceTransformer failed ({exc}); falling back to local hash vectorizer."
            )
            return [_local_hash_embedding(t, dim=384) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string using local SentenceTransformer."""
        try:
            model = _get_embed_model(self.model_name)
            embedding = model.encode(query, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as exc:
            logger.warning(
                f"SentenceTransformer query failed ({exc}); falling back to local hash vectorizer."
            )
            return _local_hash_embedding(query, dim=384)


_default_embedding_service = SentenceTransformerEmbeddingService()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Module-level batch embedding function delegating to default service."""
    return _default_embedding_service.embed_texts(texts)


def embed_query(query: str) -> list[float]:
    """Module-level query embedding function delegating to default service."""
    return _default_embedding_service.embed_query(query)

