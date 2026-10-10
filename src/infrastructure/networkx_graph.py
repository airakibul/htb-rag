"""
networkx_graph.py – GraphStore implementation using NetworkX.

Concrete adapter implementing the domain GraphStore interface.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx  # type: ignore

from src.config import GRAPH_PATH
from src.domain.interfaces import GraphStore
from src.graph.builder import load_graph
from src.graph.manifest import (
    generate_machine_manifest,
    generate_manifest_for_query,
    generate_technique_manifest,
    get_technique_manifest_for_query,
)
from src.graph.querier import (
    get_cves_for_machine,
    get_machine_details,
    get_machines_for_technique,
    get_techniques_for_category,
    get_tools_for_machine,
    query_graph,
)

logger = logging.getLogger(__name__)


class NetworkXGraphStore(GraphStore):
    """GraphStore implementation backed by a NetworkX directed graph."""

    def __init__(
        self,
        graph: nx.DiGraph | None = None,
        graph_path: str = GRAPH_PATH,
    ) -> None:
        self.graph_path = graph_path
        self.graph: nx.DiGraph = graph if graph is not None else load_graph(graph_path)

    def query_graph(self, query: str) -> dict[str, Any]:
        """Match a query string against the knowledge graph."""
        return query_graph(self.graph, query)

    def get_machines_for_technique(self, technique: str) -> list[str]:
        """Return all machines that use or demonstrate the given technique."""
        return get_machines_for_technique(self.graph, technique)

    def get_all_machines(self) -> list[str]:
        """Return sorted list of all machine node names."""
        return sorted(
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "machine"
        )

    def get_all_techniques(self) -> list[str]:
        """Return sorted list of all technique node names."""
        return sorted(
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "technique"
        )

    def get_machine_manifest(self, technique_or_category: str) -> list[dict[str, Any]]:
        """Return a compact manifest for all machines demonstrating a technique/category.

        Each entry: {"machine": str, "os": str, "difficulty": str, "techniques": list[str]}
        """
        # 1. Find the node in the graph matching technique_or_category
        # 2. If it's a category node, find all technique nodes belonging to it
        # 3. For each technique, find all machine nodes connected via 'demonstrates' edges
        # 4. For each machine, extract OS (from 'os' edge successor) and difficulty (from node attrs)
        # 5. Build and return the manifest list, sorted by machine name
        # 6. Deduplicate machines that appear under multiple techniques
        return generate_machine_manifest(self.graph, technique_or_category)

    def get_manifest_for_query(
        self,
        query: str,
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Use query_graph() to identify matched categories/techniques, 
        then build a combined manifest for all matches."""
        hits = self.query_graph(query)
        # Combine manifests from all matched categories and techniques
        # Deduplicate by machine name
        # Sort alphabetically
        return generate_manifest_for_query(self.graph, query, hits=hits, os_filter=os_filter)

    def get_technique_manifest(
        self,
        techniques: list[str],
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return a compact manifest for directly matched techniques, avoiding category expansion."""
        return generate_technique_manifest(self.graph, techniques, os_filter=os_filter)

    def get_technique_manifest_for_query(
        self,
        query: str,
        os_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return a compact manifest for directly targeted techniques or tools, avoiding broad category expansion."""
        return get_technique_manifest_for_query(self.graph, query, os_filter=os_filter)


    def get_machine_details(self, machine_name: str) -> dict[str, Any] | None:
        """Return metadata, techniques, tools, and CVEs for a single machine."""
        return get_machine_details(self.graph, machine_name)

    def get_stats(self) -> dict[str, int]:
        """Return graph node and edge counts."""
        if self.graph is None:
            return {"nodes": 0, "edges": 0}
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }

    # Convenience delegators for graph navigation
    def get_tools_for_machine(self, machine: str) -> list[str]:
        return get_tools_for_machine(self.graph, machine)

    def get_cves_for_machine(self, machine: str) -> list[str]:
        return get_cves_for_machine(self.graph, machine)

    def get_techniques_for_category(self, category: str) -> list[str]:
        return get_techniques_for_category(self.graph, category)
