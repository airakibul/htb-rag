"""
container.py – Composition Root for HTB RAG pipeline.

Centralizes dependency injection and service wiring to adhere strictly
to the Dependency Inversion Principle (DIP) and Clean Architecture.
"""

from __future__ import annotations

from typing import Any

from src.domain.interfaces import (
    EmbeddingService,
    GraphStore,
    IntentClassifier,
    LLMProvider,
    Reranker,
    VectorStore,
)
from src.infrastructure.chroma_store import ChromaStore
from src.infrastructure.cross_encoder import CrossEncoderReranker
from src.infrastructure.gemini_provider import GeminiProvider
from src.infrastructure.groq_provider import GroqProvider
from src.infrastructure.intent_router import get_intent_router
from src.infrastructure.networkx_graph import NetworkXGraphStore
from src.infrastructure.openrouter_provider import OpenRouterProvider
from src.infrastructure.sentence_transformer import SentenceTransformerEmbeddingService
from src.pipeline.retriever import HybridRetriever
from src.pipeline.synthesizer import Synthesizer


def create_vector_store() -> VectorStore:
    """Factory for default VectorStore adapter."""
    return ChromaStore()


def create_graph_store() -> GraphStore:
    """Factory for default GraphStore adapter."""
    return NetworkXGraphStore()


def create_embedding_service() -> EmbeddingService:
    """Factory for default EmbeddingService adapter."""
    return SentenceTransformerEmbeddingService()


def create_reranker() -> Reranker:
    """Factory for default Reranker adapter."""
    return CrossEncoderReranker()


def create_intent_classifier() -> IntentClassifier:
    """Factory for default IntentClassifier adapter."""
    return get_intent_router()


def create_llm_providers() -> list[LLMProvider]:
    """Factory for default LLMProvider fallback chain."""
    return [
        GroqProvider(),
        GeminiProvider(),
        OpenRouterProvider(),
    ]


def create_retriever(
    vector_store: VectorStore | None = None,
    graph_store: GraphStore | None = None,
    embedding_service: EmbeddingService | None = None,
    reranker: Reranker | None = None,
    intent_classifier: IntentClassifier | None = None,
) -> HybridRetriever:
    """Construct a fully-wired HybridRetriever instance with injected dependencies."""
    return HybridRetriever(
        vector_store=vector_store or create_vector_store(),
        graph_store=graph_store or create_graph_store(),
        embedding_service=embedding_service or create_embedding_service(),
        reranker=reranker or create_reranker(),
        intent_classifier=intent_classifier or create_intent_classifier(),
    )


def create_synthesizer(
    providers: list[LLMProvider] | None = None,
    system_prompt: str | None = None,
) -> Synthesizer:
    """Construct a fully-wired Synthesizer instance with injected dependencies."""
    kwargs: dict[str, Any] = {}
    if system_prompt is not None:
        kwargs["system_prompt"] = system_prompt
    return Synthesizer(
        providers=providers or create_llm_providers(),
        **kwargs,
    )
