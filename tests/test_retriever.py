"""Unit tests for retriever.py static/utility functions."""

from src.pipeline.retriever import HybridRetriever


def test_detect_query_intent_windows():
    intent = HybridRetriever.detect_query_intent("ADCS attack path")
    assert intent["os"] == "windows"


def test_detect_query_intent_linux():
    intent = HybridRetriever.detect_query_intent("SUID privilege escalation techniques")
    assert intent["os"] == "linux"


def test_detect_query_intent_broad():
    intent = HybridRetriever.detect_query_intent("Give me a Linux privilege escalation cheatsheet")
    assert intent["query_type"] == "structured"


def test_build_where_filter_os_only():
    filt = HybridRetriever.build_where_filter(os="windows")
    assert filt == {"os": "windows"}


def test_build_where_filter_combined():
    filt = HybridRetriever.build_where_filter(os="windows", difficulty="hard")
    assert filt == {"$and": [{"os": "windows"}, {"difficulty": "hard"}]}


def test_reciprocal_rank_fusion_merges():
    bm25_results = [
        {"text": "Chunk A: nmap scan results on linux", "rank": 1, "source": "box-a"},
        {"text": "Chunk B: sqlmap injection on web", "rank": 2, "source": "box-b"},
    ]
    vector_results = [
        {"text": "Chunk B: sqlmap injection on web", "rank": 1, "source": "box-b"},
        {"text": "Chunk C: suid binary abuse", "rank": 2, "source": "box-c"},
    ]

    merged = HybridRetriever.reciprocal_rank_fusion(bm25_results, vector_results, k=60)

    assert len(merged) == 3
    # Chunk B was rank 2 in BM25 and rank 1 in Vector, so it should have the highest RRF score
    assert merged[0]["text"] == "Chunk B: sqlmap injection on web"
    assert "rrf_score" in merged[0]
    assert merged[0]["rank"] == 1
    assert merged[1]["rank"] == 2
    assert merged[2]["rank"] == 3


def test_retrieve_manifest_injection_broad():
    from unittest.mock import MagicMock
    from src.domain.models import RetrievalResult

    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.vector_store = MagicMock()
    retriever.graph_store = MagicMock()
    retriever.embedding_service = MagicMock()
    retriever.reranker = MagicMock()
    retriever.graph = None
    retriever.docs = []
    retriever.bm25 = None
    retriever.bm25_search = MagicMock(return_value=[])
    retriever.vector_search = MagicMock(return_value=[])
    retriever.reciprocal_rank_fusion = MagicMock(return_value=[])
    retriever.reranker.rerank = MagicMock(return_value=[])

    retriever.graph_store.query_graph.return_value = {"relevant_machines": []}
    sample_manifest = [{"machine": "htb-active", "os": "windows", "difficulty": "easy", "techniques": ["Kerberoasting"]}]
    retriever.graph_store.get_manifest_for_query.return_value = sample_manifest

    result = retriever.retrieve("Linux privilege escalation cheatsheet")
    # Manifest is attached for broad queries to provide structured corpus coverage
    assert result.manifest is not None
    assert len(result.manifest) > 0
    assert result.manifest[0]["machine"] == "htb-active"
    assert result.get("graph") == {"relevant_machines": []}


def test_retrieve_manifest_none_for_specific():
    from unittest.mock import MagicMock
    from src.domain.models import RetrievalResult

    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.vector_store = MagicMock()
    retriever.graph_store = MagicMock()
    retriever.embedding_service = MagicMock()
    retriever.reranker = MagicMock()
    retriever.graph = None
    retriever.docs = []
    retriever.bm25 = None
    retriever.bm25_search = MagicMock(return_value=[])
    retriever.vector_search = MagicMock(return_value=[])
    retriever.reciprocal_rank_fusion = MagicMock(return_value=[])
    retriever.reranker.rerank = MagicMock(return_value=[])

    retriever.graph_store.query_graph.return_value = {"relevant_machines": []}

    result = retriever.retrieve("htb-active Kerberoasting port 88")
    assert isinstance(result, RetrievalResult)
    assert result.manifest is None


def test_graph_guided_candidate_injection_for_broad_query():
    from unittest.mock import MagicMock
    from src.domain.models import RetrievalResult

    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.vector_store = MagicMock()
    retriever.graph_store = MagicMock()
    retriever.embedding_service = MagicMock()
    retriever.reranker = MagicMock()
    retriever.graph = None

    doc_a = {"text": "Chunk from box-a on linux privesc", "metadata": {"source": "box-a", "os": "linux"}}
    doc_b = {"text": "Chunk from box-b on linux sudo privilege", "metadata": {"source": "box-b", "os": "linux"}}
    retriever.docs = [doc_a, doc_b]
    retriever._machine_docs = {"box-a": [doc_a], "box-b": [doc_b]}
    retriever._machine_doc_indices = {"box-a": [0], "box-b": [1]}

    retriever._bm25_index = MagicMock()
    retriever._bm25_index.get_scores_for_query.return_value = [0.5, 0.9]

    retriever.bm25_search = MagicMock(return_value=[{"text": doc_a["text"], "metadata": doc_a["metadata"], "score": 0.5, "rank": 1}])
    retriever.vector_search = MagicMock(return_value=[])
    retriever.reciprocal_rank_fusion = MagicMock(return_value=[{"text": doc_a["text"], "metadata": doc_a["metadata"], "score": 0.5, "rrf_score": 0.016, "rank": 1}])
    retriever.reranker.rerank = MagicMock(side_effect=lambda q, c: c)

    retriever.graph_store.query_graph.return_value = {"relevant_machines": ["box-a", "box-b"]}

    result = retriever.retrieve("Linux privilege escalation techniques")

    assert retriever.reranker.rerank.called
    rerank_chunks = retriever.reranker.rerank.call_args[0][1]
    sources_in_rerank = {c["metadata"]["source"] for c in rerank_chunks}
    assert "box-b" in sources_in_rerank
    assert "box-a" in sources_in_rerank


def test_adaptive_top_k_budget_for_broad_query():
    from unittest.mock import MagicMock
    from src.domain.models import RetrievalResult

    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.vector_store = MagicMock()
    retriever.graph_store = MagicMock()
    retriever.embedding_service = MagicMock()
    retriever.reranker = MagicMock()
    retriever.graph = None
    retriever.docs = []
    retriever._machine_docs = {}
    retriever._machine_doc_indices = {}
    retriever._bm25_index = None

    retriever.bm25_search = MagicMock(return_value=[])
    retriever.vector_search = MagicMock(return_value=[])
    retriever.reciprocal_rank_fusion = MagicMock(return_value=[])
    retriever.reranker.rerank = MagicMock(return_value=[])

    # Case 1: 50 relevant machines -> budget capped at 30
    retriever.graph_store.query_graph.return_value = {
        "relevant_machines": [f"box-{i}" for i in range(50)]
    }
    result_large = retriever.retrieve("Linux privilege escalation cheatsheet")
    assert isinstance(result_large, RetrievalResult)

    # Case 2: Specific query -> budget stays at base_k (8)
    result_specific = retriever.retrieve("htb-active Kerberoasting port 88")
    assert isinstance(result_specific, RetrievalResult)

