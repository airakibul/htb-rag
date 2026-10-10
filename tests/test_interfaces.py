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
    assert hasattr(NetworkXGraphStore, "get_machine_details")
    assert hasattr(NetworkXGraphStore, "get_stats")


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


def test_networkx_graph_store_machine_details_and_stats():
    import networkx as nx
    g = nx.DiGraph()
    g.add_node("htb-testbox", type="machine", difficulty="Easy")
    g.add_node("windows", type="os")
    g.add_node("Kerberoasting", type="technique")
    g.add_node("nmap", type="tool")
    g.add_node("CVE-2021-44228", type="cve")
    g.add_edge("htb-testbox", "windows", rel="os")
    g.add_edge("htb-testbox", "Kerberoasting", rel="demonstrates")
    g.add_edge("htb-testbox", "nmap", rel="uses")
    g.add_edge("htb-testbox", "CVE-2021-44228", rel="vulnerable_to")

    store = NetworkXGraphStore(graph=g)
    stats = store.get_stats()
    assert stats["nodes"] == 5
    assert stats["edges"] == 4

    details = store.get_machine_details("htb-testbox")
    assert details is not None
    assert details["machine"] == "htb-testbox"
    assert details["os"] == "windows"
    assert "Kerberoasting" in details["techniques"]
    assert "nmap" in details["tools"]
    assert "CVE-2021-44228" in details["cves"]

    assert store.get_machine_details("non-existent") is None


def test_container_factories():
    from src.container import (
        create_vector_store,
        create_graph_store,
        create_embedding_service,
        create_reranker,
        create_llm_providers,
    )
    assert isinstance(create_vector_store(), VectorStore)
    assert isinstance(create_graph_store(), GraphStore)
    assert isinstance(create_embedding_service(), EmbeddingService)
    assert isinstance(create_reranker(), Reranker)
    providers = create_llm_providers()
    assert len(providers) >= 3
    assert all(isinstance(p, LLMProvider) for p in providers)


def test_ingestion_pipeline_initialization():
    from unittest.mock import MagicMock
    from src.pipeline.ingest import IngestionPipeline

    mock_store = MagicMock(spec=VectorStore)
    mock_embed = MagicMock(spec=EmbeddingService)
    mock_chunk = MagicMock(spec=ChunkingStrategy)

    pipeline = IngestionPipeline(
        vector_store=mock_store,
        embedding_service=mock_embed,
        chunking_strategy=mock_chunk,
    )
    assert pipeline.vector_store is mock_store
    assert pipeline.embedding_service is mock_embed
    assert pipeline.chunking_strategy is mock_chunk


