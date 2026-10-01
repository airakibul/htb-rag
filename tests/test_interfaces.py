"""Unit tests for domain interfaces and their concrete implementations."""

import pytest

from src.domain.interfaces import (
    ChunkingStrategy,
    EmbeddingService,
    GraphStore,
    LLMProvider,
    Reranker,
    VectorStore,
)
from src.infrastructure.chroma_store import ChromaStore
from src.infrastructure.cross_encoder import CrossEncoderReranker
from src.infrastructure.gemini_provider import GeminiProvider
from src.infrastructure.groq_provider import GroqProvider
from src.infrastructure.networkx_graph import NetworkXGraphStore
from src.infrastructure.sentence_transformer import SentenceTransformerEmbeddingService
from src.pipeline.chunker import MarkdownChunker


def test_abstract_classes_cannot_be_instantiated():
    abstract_classes = [
        VectorStore,
        GraphStore,
        EmbeddingService,
        LLMProvider,
        Reranker,
        ChunkingStrategy,
    ]
    for cls in abstract_classes:
        with pytest.raises(TypeError):
            cls()  # type: ignore[abstract]


def test_concrete_implementations_satisfy_contracts():
    # VectorStore
    assert issubclass(ChromaStore, VectorStore)
    assert hasattr(ChromaStore, "query")
    assert hasattr(ChromaStore, "get_all_documents")
    assert hasattr(ChromaStore, "upsert")

    # GraphStore
    assert issubclass(NetworkXGraphStore, GraphStore)
    assert hasattr(NetworkXGraphStore, "query_graph")
    assert hasattr(NetworkXGraphStore, "get_machines_for_technique")
    assert hasattr(NetworkXGraphStore, "get_all_machines")
    assert hasattr(NetworkXGraphStore, "get_all_techniques")
    assert hasattr(NetworkXGraphStore, "get_machine_manifest")
    assert hasattr(NetworkXGraphStore, "get_manifest_for_query")
    assert hasattr(NetworkXGraphStore, "get_technique_manifest")
    assert hasattr(NetworkXGraphStore, "get_technique_manifest_for_query")


    # EmbeddingService
    assert issubclass(SentenceTransformerEmbeddingService, EmbeddingService)
    assert hasattr(SentenceTransformerEmbeddingService, "embed_texts")
    assert hasattr(SentenceTransformerEmbeddingService, "embed_query")

    # LLMProvider
    assert issubclass(GroqProvider, LLMProvider)
    assert hasattr(GroqProvider, "generate")
    assert issubclass(GeminiProvider, LLMProvider)
    assert hasattr(GeminiProvider, "generate")

    # Reranker
    assert issubclass(CrossEncoderReranker, Reranker)
    assert hasattr(CrossEncoderReranker, "rerank")

    # ChunkingStrategy
    assert issubclass(MarkdownChunker, ChunkingStrategy)
    assert hasattr(MarkdownChunker, "chunk_file")
    assert hasattr(MarkdownChunker, "chunk_text")
