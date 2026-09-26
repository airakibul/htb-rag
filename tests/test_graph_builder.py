"""Unit tests for graph_builder.py."""

from src.graph_builder import build_graph, query_graph


def test_build_graph_creates_machine_nodes(sample_chunks: list[dict]):
    graph = build_graph(sample_chunks)
    assert "htb-testbox" in graph
    assert graph.nodes["htb-testbox"]["type"] == "machine"
    assert "htb-winbox" in graph
    assert graph.nodes["htb-winbox"]["type"] == "machine"


def test_build_graph_creates_tool_edges(sample_chunks: list[dict]):
    graph = build_graph(sample_chunks)
    assert "nmap" in graph
    assert graph.nodes["nmap"]["type"] == "tool"
    assert graph.has_edge("htb-testbox", "nmap")
    assert graph.edges["htb-testbox", "nmap"]["rel"] == "uses"


def test_build_graph_os_edge(sample_chunks: list[dict]):
    graph = build_graph(sample_chunks)
    assert "linux" in graph
    assert graph.nodes["linux"]["type"] == "os"
    assert graph.has_edge("htb-testbox", "linux")
    assert graph.edges["htb-testbox", "linux"]["rel"] == "os"

    assert "windows" in graph
    assert graph.nodes["windows"]["type"] == "os"
    assert graph.has_edge("htb-winbox", "windows")


def test_query_graph_matches_tools(sample_chunks: list[dict]):
    graph = build_graph(sample_chunks)
    result = query_graph(graph, "how to use nmap on linux?")
    assert "nmap" in result["matched_tools"]
    assert "htb-testbox" in result["relevant_machines"]


def test_query_graph_empty(sample_chunks: list[dict]):
    graph = build_graph(sample_chunks)
    result = query_graph(graph, "something completely unrelated and unknown")
    assert result["matched_tools"] == []
    assert result["matched_cves"] == []
    assert result["relevant_machines"] == []
    assert "technique_machines" in result
    assert result["technique_machines"] == {}


def test_query_graph_returns_technique_machines(sample_chunks: list[dict]):
    graph = build_graph(sample_chunks)
    result = query_graph(graph, "SUID privilege escalation")
    assert "technique_machines" in result
    assert isinstance(result["technique_machines"], dict)
