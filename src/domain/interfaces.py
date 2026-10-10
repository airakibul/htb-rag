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
    def get_machine_manifest(self, technique_or_category: str) -> list[dict[str, Any]]:
        """Return a compact manifest for all machines demonstrating a technique/category."""
        ...

    @abstractmethod
    def get_manifest_for_query(
        self,
        query: str,
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Use query_graph() to identify matched categories/techniques, then build a combined manifest."""
        ...

    @abstractmethod
    def get_technique_manifest(
        self,
        techniques: list[str],
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return a compact manifest for only directly matched techniques, without category expansion."""
        ...

    @abstractmethod
    def get_technique_manifest_for_query(
        self,
        query: str,
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return a compact manifest for directly targeted techniques or tools, avoiding broad category expansion."""
        ...

    @abstractmethod
    def get_machine_details(self, machine_name: str) -> dict[str, Any] | None:
        """Return metadata, techniques, tools, and CVEs for a single machine."""
        ...

    @abstractmethod
    def get_stats(self) -> dict[str, int]:
        """Return graph node and edge counts."""
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


class IntentClassifier(ABC):
    """Abstract interface for query intent classification and routing."""

    @abstractmethod
    def classify_intent(self, query: str) -> dict[str, Any]:
        """Classify query into scope (broad/specific), target OS, and phase."""
        ...

