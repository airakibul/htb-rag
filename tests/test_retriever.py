"""Unit tests for retriever.py static/utility functions."""

from src.retriever import HybridRetriever


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
