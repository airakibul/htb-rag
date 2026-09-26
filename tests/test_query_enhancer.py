"""Unit tests for query_enhancer.py."""

import networkx as nx
import pytest
from src.query_enhancer import enhance_query


def test_enhance_detects_broad_scope():
    res = enhance_query("Windows privilege escalation cheatsheet")
    assert res.query_scope == "broad"


def test_enhance_detects_os():
    res = enhance_query("Linux privesc")
    assert res.target_os == "linux"


def test_enhance_detects_phase():
    res = enhance_query("privilege escalation")
    assert res.target_phase == "privesc"


def test_enhance_expands_cve(monkeypatch):
    mock_graph = nx.DiGraph()
    mock_graph.add_node("CVE-2017-0143", type="cve", aliases=["eternalblue", "ms17-010"])

    # Test with explicitly provided graph
    res_with_graph = enhance_query("CVE-2017-0143", graph=mock_graph)
    terms_with_graph = [t.lower() for t in res_with_graph.expanded_terms]
    assert any("eternalblue" in t or "ms17-010" in t for t in terms_with_graph)

    # Test with default load_graph via fallback
    import src.query_enhancer as qe
    monkeypatch.setattr(qe, "load_graph", lambda: mock_graph)
    res_default = enhance_query("CVE-2017-0143")
    terms_default = [t.lower() for t in res_default.expanded_terms]
    assert any("eternalblue" in t or "ms17-010" in t for t in terms_default)


def test_enhance_specific_scope():
    res = enhance_query("How does DCSync work")
    assert res.query_scope == "specific"
