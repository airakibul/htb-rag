"""
interfaces.py – Abstract base classes defining domain interfaces.

Follows Interface Segregation and Dependency Inversion principles.
Concrete implementations live in `src.infrastructure`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class VectorStore(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    def query(
        self, embedding: list[float], top_k: int, where: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Query vector index by embedding vector."""
        ...

    @abstractmethod
    def get_all_documents(self) -> list[dict[str, Any]]:
        """Return every document stored in the vector collection."""
        ...

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert documents with their embeddings and metadata."""
        ...


class GraphStore(ABC):
    """Abstract interface for knowledge graph operations."""

    @abstractmethod
    def query_graph(self, query: str) -> dict[str, Any]:
        """Match a query string against the knowledge graph."""
        ...

    @abstractmethod
    def get_machines_for_technique(self, technique: str) -> list[str]:
        """Return all machines that use or demonstrate the given technique."""
        ...

    @abstractmethod
    def get_all_machines(self) -> list[str]:
        """Return sorted list of all machine node names."""
        ...

    @abstractmethod
    def get_all_techniques(self) -> list[str]:
        """Return sorted list of all technique node names."""
        ...

    @abstractmethod
    def get_machine_manifest(self, technique: str) -> list[dict[str, Any]]:
        """NEW: Return a compact manifest table for all machines demonstrating a technique."""
        ...


class EmbeddingService(ABC):
    """Abstract interface for generating text embeddings."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple texts."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        ...


class LLMProvider(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1800,
        temperature: float = 0.1,
    ) -> str | None:
        """Generate text from system and user prompts. Returns None on failure."""
        ...


class Reranker(ABC):
    """Abstract interface for document re-ranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Re-rank candidate chunks against query."""
        ...


class ChunkingStrategy(ABC):
    """Abstract interface for document chunking strategies."""

    @abstractmethod
    def chunk_file(self, file_path: str | Path) -> list[dict[str, Any]]:
        """Chunk a file from disk into structured chunk dicts."""
        ...

    @abstractmethod
    def chunk_text(
        self, text: str, source: str = "", **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Chunk raw text into structured chunk dicts."""
        ...
