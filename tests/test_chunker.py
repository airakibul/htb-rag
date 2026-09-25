"""Unit tests for chunker.py."""

from pathlib import Path
from src.chunker import chunk_file


def test_normal_writeup_produces_chunks(sample_writeup_normal: Path):
    chunks = chunk_file(str(sample_writeup_normal))
    assert len(chunks) >= 4


def test_stub_file_detection(sample_writeup_stub: Path):
    chunks = chunk_file(str(sample_writeup_stub))
    assert len(chunks) > 0
    assert all(c["stub_file"] is True for c in chunks)


def test_stuck_heading_fix(sample_writeup_stuck_headings: Path):
    chunks = chunk_file(str(sample_writeup_stuck_headings))
    # Stuck headings "## Recon" and "## Foothold" should be separated and chunked
    assert len(chunks) >= 2
    h2_sections = {c["h2"] for c in chunks}
    assert "Recon" in h2_sections
    assert "Foothold" in h2_sections


def test_os_detection_linux(sample_writeup_normal: Path):
    chunks = chunk_file(str(sample_writeup_normal))
    assert len(chunks) > 0
    assert all(c["os"] == "linux" for c in chunks)


def test_os_detection_windows(tmp_path: Path):
    content = "# HTB - WinTarget\n\n## Box Info\n\n| OS | Difficulty |\n|---|---|\n| Windows | Easy |\n\n## Recon\n\nScanned ports."
    p = tmp_path / "htb-wintarget.md"
    p.write_text(content, encoding="utf-8")
    chunks = chunk_file(str(p))
    assert len(chunks) > 0
    assert all(c["os"] == "windows" for c in chunks)


def test_difficulty_extraction(sample_writeup_normal: Path):
    chunks = chunk_file(str(sample_writeup_normal))
    assert len(chunks) > 0
    assert all(c["difficulty"] == "medium" for c in chunks)


def test_context_prefix_injection(sample_writeup_normal: Path):
    chunks = chunk_file(str(sample_writeup_normal))
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["text"].startswith("[Machine: ")


def test_code_fence_integrity(sample_writeup_normal: Path):
    chunks = chunk_file(str(sample_writeup_normal))
    for chunk in chunks:
        # Every chunk should have balanced triple backticks
        assert chunk["text"].count("```") % 2 == 0


def test_ignore_headings(sample_writeup_normal: Path):
    chunks = chunk_file(str(sample_writeup_normal))
    # Chunks from ## Box Info should be ignored
    assert not any(c["h2"].lower() == "box info" for c in chunks)
