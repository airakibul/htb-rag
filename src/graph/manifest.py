"""
manifest.py – Graph-Assisted Manifest Generator.

Extracts compact machine-technique metadata manifests from the knowledge graph
to inject into LLM context, boosting recall without context overflow.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from src.graph.querier import get_machines_for_technique

logger = logging.getLogger(__name__)


def generate_machine_manifest(
    graph: nx.DiGraph,
    technique: str,
) -> list[dict[str, Any]]:
    """Return a compact manifest table for all machines demonstrating a technique.

    Parameters
    ----------
    graph : nx.DiGraph
        The HTB knowledge graph.
    technique : str
        Target technique name.

    Returns
    -------
    list[dict[str, Any]]
        List of machine manifest entries with keys:
        - machine: name of the machine
        - os: target OS ("windows", "linux", "unknown")
        - difficulty: difficulty rating or "unknown"
        - technique: the matching technique
    """
    machines = get_machines_for_technique(graph, technique)
    manifest: list[dict[str, Any]] = []

    for m in machines:
        # Resolve OS from outgoing "os" edge
        os_val = "unknown"
        for succ in graph.successors(m):
            if graph.edges[m, succ].get("rel") == "os":
                os_val = succ
                break

        node_data = graph.nodes[m] if m in graph else {}
        diff_val = node_data.get("difficulty", "unknown")

        manifest.append({
            "machine": m,
            "os": os_val,
            "difficulty": diff_val,
            "technique": technique,
        })

    return manifest
