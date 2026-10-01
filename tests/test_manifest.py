"""Unit tests for manifest generation logic."""

import networkx as nx
import pytest

from src.graph.manifest import generate_machine_manifest, generate_manifest_for_query
from src.infrastructure.networkx_graph import NetworkXGraphStore


@pytest.fixture
def mock_manifest_graph() -> nx.DiGraph:
    """Build a controlled test graph for manifest verification."""
    g = nx.DiGraph()

    # Category: Active Directory
    g.add_node("Active Directory", type="category")

    # Techniques
    g.add_node("Kerberoasting", type="technique")
    g.add_node("DCSync", type="technique")
    g.add_edge("Kerberoasting", "Active Directory", rel="category")
    g.add_edge("DCSync", "Active Directory", rel="category")

    # OS nodes
    g.add_node("windows", type="os")
    g.add_node("linux", type="os")

    # 5 machines demonstrating Kerberoasting
    machines = ["htb-box1", "htb-box2", "htb-box3", "htb-box4", "htb-box5"]
    for m in machines:
        g.add_node(m, type="machine", difficulty="Medium")
        g.add_edge(m, "Kerberoasting", rel="demonstrates")
        g.add_edge(m, "windows", rel="os")

    # htb-box1 also demonstrates DCSync (test deduplication)
    g.add_edge("htb-box1", "DCSync", rel="demonstrates")

    # Another machine demonstrating DCSync
    g.add_node("htb-box6", type="machine", difficulty="Hard")
    g.add_edge("htb-box6", "DCSync", rel="demonstrates")
    g.add_edge("htb-box6", "windows", rel="os")

    # Linux machine with unrelated technique
    g.add_node("SUID Privesc", type="technique")
    g.add_node("htb-linuxbox", type="machine", difficulty="Easy")
    g.add_edge("htb-linuxbox", "SUID Privesc", rel="demonstrates")
    g.add_edge("htb-linuxbox", "linux", rel="os")

    return g


def test_manifest_returns_all_machines_for_technique(mock_manifest_graph):
    # Given a graph with 5 machines linked to "Kerberoasting"
    # When get_machine_manifest("Kerberoasting") is called
    manifest = generate_machine_manifest(mock_manifest_graph, "Kerberoasting")
    # Then all 5 machines should be in the result
    machine_names = {m["machine"] for m in manifest}
    expected = {"htb-box1", "htb-box2", "htb-box3", "htb-box4", "htb-box5"}
    assert expected.issubset(machine_names)
    assert len(manifest) == 5
    for item in manifest:
        assert item["os"] == "windows"
        assert item["difficulty"] == "Medium"
        assert "Kerberoasting" in item["techniques"]


def test_manifest_deduplicates_machines(mock_manifest_graph):
    # Machine linked to multiple techniques should appear once
    manifest = generate_machine_manifest(mock_manifest_graph, "Active Directory")
    machines = [m["machine"] for m in manifest]
    # Check that machines appear only once (deduplicated)
    assert len(machines) == len(set(machines))
    assert "htb-box1" in machines
    # Check that htb-box1 lists both techniques
    box1 = next(m for m in manifest if m["machine"] == "htb-box1")
    assert "Kerberoasting" in box1["techniques"]
    assert "DCSync" in box1["techniques"]


def test_manifest_for_broad_query(mock_manifest_graph):
    # "Active Directory attack techniques" should return all AD machines from graph
    manifest = generate_manifest_for_query(
        mock_manifest_graph,
        "Active Directory attack techniques",
    )
    machines = {m["machine"] for m in manifest}
    assert {"htb-box1", "htb-box2", "htb-box3", "htb-box4", "htb-box5", "htb-box6"}.issubset(machines)
    assert "htb-linuxbox" not in machines


def test_manifest_os_filter(mock_manifest_graph):
    # Requesting Linux on AD should yield no machines since all AD boxes are Windows
    manifest_linux = generate_manifest_for_query(
        mock_manifest_graph,
        "Active Directory attack techniques",
        os_filter="linux",
    )
    assert len(manifest_linux) == 0

    # Requesting Windows should yield the AD machines
    manifest_win = generate_manifest_for_query(
        mock_manifest_graph,
        "Active Directory attack techniques",
        os_filter="windows",
    )
    assert len(manifest_win) == 6


def test_graph_store_manifest_methods(mock_manifest_graph):
    store = NetworkXGraphStore(graph=mock_manifest_graph)
    manifest = store.get_machine_manifest("Kerberoasting")
    assert len(manifest) == 5

    query_manifest = store.get_manifest_for_query("Active Directory attack techniques")
    assert len(query_manifest) == 6

    # Technique-specific manifest tests
    tech_manifest = store.get_technique_manifest(["Kerberoasting"])
    assert len(tech_manifest) == 5
    assert all("Kerberoasting" in m["techniques"] for m in tech_manifest)

    listing_manifest = store.get_technique_manifest_for_query(
        "How does Kerberoasting work in Active Directory and which machines demonstrate it?"
    )
    assert len(listing_manifest) == 5

