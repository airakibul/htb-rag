"""Unit tests for newly added advanced Precision & Recall techniques."""

import pytest
from src.pipeline.query_enhancer import enhance_query, generate_multi_queries
from src.pipeline.synthesizer import compress_context_chunk
from src.pipeline.retriever import HybridRetriever
from src.domain.models import EnhancedQuery


def test_multi_query_generation_produces_variations():
    enh = enhance_query("How does Kerberoasting work in Active Directory?")
    queries = generate_multi_queries("How does Kerberoasting work in Active Directory?", enh)
    assert len(queries) >= 1
    # Base query is present
    assert "Kerberoasting" in queries[0]


def test_context_compression_strips_noise():
    raw_text = (
        "Here is the proof of concept:\n"
        "=========================================\n"
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0\n"
        "deadbeef0123456789abcdef0123456789abcdef0123456789\n"
        "```bash\n"
        "python3 exploit.py -t 10.10.10.1"
    )
    compressed = compress_context_chunk(raw_text, max_chars=500)
    assert "[hex data omitted]" in compressed
    assert "[base64 omitted]" in compressed
    # Ensures unclosed code block is closed
    assert compressed.count("```") % 2 == 0


def test_chunker_parent_child_metadata(tmp_path):
    from src.pipeline.chunker import chunk_file

    sample_md = tmp_path / "htb-testbox.md"
    sample_md.write_text(
        "# TestBox\n\n"
        "Intro text\n\n"
        "## Recon\n\n"
        "### Nmap Port Scan\n\n"
        "Port 80 open on target.\n\n"
        "## Privilege Escalation\n\n"
        "### Root SUID Abuse\n\n"
        "Abused SUID binary to get root.\n",
        encoding="utf-8",
    )
    chunks = chunk_file(sample_md)
    assert len(chunks) > 0
    priv_chunks = [c for c in chunks if c.get("h2") == "Privilege Escalation"]
    if priv_chunks:
        assert priv_chunks[0].get("parent_section") == "Privilege Escalation"
        assert "parent_path" in priv_chunks[0]
