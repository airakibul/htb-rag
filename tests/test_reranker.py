"""Unit tests for reranker.py."""

from src.reranker import rerank


def test_rerank_returns_same_length():
    chunks = [
        {"text": "Nmap scan found port 80 and 443", "source": "box1", "os": "linux"},
        {"text": "SQL injection vulnerability in login form", "source": "box2", "os": "windows"},
        {"text": "Privilege escalation via sudo rights", "source": "box3", "os": "linux"},
    ]
    res = rerank("nmap scan", chunks)
    assert len(res) == len(chunks)


def test_rerank_empty_input():
    res = rerank("test query", [])
    assert res == []


def test_rerank_preserves_metadata():
    chunks = [
        {
            "text": "Nmap scan results on linux target",
            "source": "box1",
            "os": "linux",
            "difficulty": "easy",
            "custom_attr": "important_flag",
        },
    ]
    res = rerank("nmap scan", chunks)
    assert len(res) == 1
    chunk = res[0]
    assert chunk["source"] == "box1"
    assert chunk["os"] == "linux"
    assert chunk["difficulty"] == "easy"
    assert chunk["custom_attr"] == "important_flag"
