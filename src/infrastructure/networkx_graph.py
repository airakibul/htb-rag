"""
networkx_graph.py – GraphStore implementation using NetworkX.

Concrete adapter implementing the domain GraphStore interface.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from src.config import GRAPH_PATH
from src.domain.interfaces import GraphStore
from src.graph.builder import load_graph
from src.graph.manifest import generate_machine_manifest
from src.graph.querier import (
    get_cves_for_machine,
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

    def get_machine_manifest(self, technique: str) -> list[dict[str, Any]]:
        """Return a compact manifest table for all machines demonstrating a technique."""
        return generate_machine_manifest(self.graph, technique)

    # Convenience delegators for graph navigation
    def get_tools_for_machine(self, machine: str) -> list[str]:
        return get_tools_for_machine(self.graph, machine)

    def get_cves_for_machine(self, machine: str) -> list[str]:
        return get_cves_for_machine(self.graph, machine)

    def get_techniques_for_category(self, category: str) -> list[str]:
        return get_techniques_for_category(self.graph, category)
