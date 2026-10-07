"""
manifest.py – Graph-Assisted Manifest Generator.

Extracts compact machine-technique metadata manifests from the knowledge graph
to inject into LLM context, boosting recall without context overflow.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import networkx as nx

from src.graph.querier import query_graph

logger = logging.getLogger(__name__)


def _find_graph_node(graph: nx.DiGraph, name: str) -> str | None:
    """Find a node in the graph by exact, case-insensitive, alias, or normalized matching."""
    if not name or not isinstance(name, str):
        return None
    if name in graph:
        return name
    target_low = name.lower().strip()
    # 1. Direct case-insensitive match on node names
    for n in graph.nodes():
        if str(n).lower() == target_low:
            return str(n)
    # 2. Alias match
    for n, d in graph.nodes(data=True):
        aliases = [str(a).lower() for a in d.get("aliases", [])]
        if target_low in aliases:
            return str(n)
    # 3. Normalized hyphens and spaces (e.g. "windows privesc" -> "Windows-Privesc")
    target_norm = target_low.replace(" ", "-").replace("_", "-")
    for n in graph.nodes():
        if str(n).lower().replace(" ", "-").replace("_", "-") == target_norm:
            return str(n)
    return None


GENERIC_TECHNIQUES: set[str] = {
    "exploit",
    "exploitation",
    "intended",
    "shortcut",
    "privesc",
    "privilege escalation",
    "escalation",
    "template injection",
    "server side template injection",
}


def generate_machine_manifest(
    graph: nx.DiGraph,
    technique_or_category: str,
) -> list[dict[str, Any]]:
    """Return a compact manifest for all machines demonstrating a technique, tool, CVE, or category.

    Parameters
    ----------
    graph : nx.DiGraph
        The HTB knowledge graph.
    technique_or_category : str
        Target technique, tool, CVE name, or domain category.

    Returns
    -------
    list[dict[str, Any]]
        List of machine manifest entries with keys:
        - machine: name of the machine
        - os: target OS ("windows", "linux", "unknown")
        - difficulty: difficulty rating or "unknown"
        - techniques: list of demonstrated techniques
    """
    if not technique_or_category or not isinstance(technique_or_category, str):
        return []

    # 1. Find the node in the graph matching technique_or_category
    matched_node = _find_graph_node(graph, technique_or_category)
    if not matched_node or matched_node not in graph:
        return []

    # 2. If it's a category node, find all technique nodes belonging to it
    node_type = graph.nodes[matched_node].get("type")
    if node_type == "category":
        targets = sorted(
            t for t in graph.predecessors(matched_node)
            if graph.nodes[t].get("type") == "technique"
            and str(t).lower().strip() not in GENERIC_TECHNIQUES
        )
    elif node_type in ("technique", "tool", "cve"):
        targets = [matched_node]
    else:
        tech_preds = [
            t for t in graph.predecessors(matched_node)
            if graph.nodes[t].get("type") == "technique"
        ]
        targets = sorted(tech_preds) if tech_preds else [matched_node]

    # 3. For each target, find all machine nodes connected via relevant edges
    machine_map: dict[str, dict[str, Any]] = {}
    for target in targets:
        # Predecessors: machine -> target
        for p in graph.predecessors(target):
            if graph.nodes[p].get("type") != "machine":
                continue
            rel = str(graph.edges[p, target].get("rel", ""))
            if any(r in rel for r in ("demonstrate", "use", "exploit")):
                m = p
                if m not in machine_map:
                    os_val = "unknown"
                    for succ in graph.successors(m):
                        if graph.edges[m, succ].get("rel") == "os":
                            os_val = succ
                            break
                    if os_val == "unknown":
                        os_val = str(graph.nodes[m].get("os", "unknown") or "unknown")

                    diff_val = str(graph.nodes[m].get("difficulty", "unknown") or "unknown")

                    machine_map[m] = {
                        "machine": m,
                        "os": os_val,
                        "difficulty": diff_val,
                        "techniques": set(),
                    }
                machine_map[m]["techniques"].add(target)

        # Successors: target -> machine (if any)
        for succ in graph.successors(target):
            if graph.nodes[succ].get("type") != "machine":
                continue
            rel = str(graph.edges[target, succ].get("rel", ""))
            if any(r in rel for r in ("demonstrate", "use", "exploit")):
                m = succ
                if m not in machine_map:
                    os_val = "unknown"
                    for o_succ in graph.successors(m):
                        if graph.edges[m, o_succ].get("rel") == "os":
                            os_val = o_succ
                            break
                    if os_val == "unknown":
                        os_val = str(graph.nodes[m].get("os", "unknown") or "unknown")

                    diff_val = str(graph.nodes[m].get("difficulty", "unknown") or "unknown")

                    machine_map[m] = {
                        "machine": m,
                        "os": os_val,
                        "difficulty": diff_val,
                        "techniques": set(),
                    }
                machine_map[m]["techniques"].add(target)

    # 4. Build and return the manifest list, sorted by machine name
    manifest = [
        {
            "machine": m,
            "os": data["os"],
            "difficulty": data["difficulty"],
            "techniques": sorted(data["techniques"]),
        }
        for m, data in sorted(machine_map.items())
    ]
    return manifest


def generate_manifest_for_query(
    graph: nx.DiGraph,
    query: str,
    hits: dict[str, Any] | None = None,
    os_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Use query_graph() to identify matched categories/techniques,
    then build a combined manifest for all matches.
    """
    if hits is None:
        hits = query_graph(graph, query)

    matched_categories = list(hits.get("matched_categories", []))
    matched_techniques = list(hits.get("matched_techniques", []))

    low = query.lower()
    # Target OS resolution
    target_os = os_filter
    if not target_os:
        if "windows" in low and "linux" not in low:
            target_os = "windows"
        elif "linux" in low and "windows" not in low:
            target_os = "linux"
        elif "active directory" in low or "adcs" in low:
            target_os = "windows"

    combined: dict[str, dict[str, Any]] = {}

    specific_techniques = [
        t for t in matched_techniques
        if str(t).lower().strip() not in GENERIC_TECHNIQUES
    ]
    target_entities = specific_techniques if specific_techniques else matched_categories

    for entity in target_entities:
        for entry in generate_machine_manifest(graph, entity):
            m = entry["machine"]
            if target_os and entry.get("os") not in (target_os, "unknown"):
                continue
            if m not in combined:
                combined[m] = {
                    "machine": m,
                    "os": entry["os"],
                    "difficulty": entry["difficulty"],
                    "techniques": set(entry["techniques"]),
                }
            else:
                combined[m]["techniques"].update(entry["techniques"])

    return [
        {
            "machine": m,
            "os": data["os"],
            "difficulty": data["difficulty"],
            "techniques": sorted(data["techniques"]),
        }
        for m, data in sorted(combined.items())
    ]


def generate_technique_manifest(
    graph: nx.DiGraph,
    techniques: list[str],
    os_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Return a compact manifest for all machines demonstrating any of the given techniques/tools/CVEs.

    Generic graph traversal over verified relationships without hardcoded tool special-cases.
    """
    combined: dict[str, dict[str, Any]] = {}
    for tech in techniques:
        if str(tech).lower().strip() in GENERIC_TECHNIQUES:
            continue
        for entry in generate_machine_manifest(graph, tech):
            m = entry["machine"]
            if os_filter and entry.get("os") not in (os_filter, "unknown"):
                continue
            if m not in combined:
                combined[m] = {
                    "machine": m,
                    "os": entry["os"],
                    "difficulty": entry["difficulty"],
                    "techniques": set(entry["techniques"]),
                }
            else:
                combined[m]["techniques"].update(entry["techniques"])

    return [
        {
            "machine": m,
            "os": data["os"],
            "difficulty": data["difficulty"],
            "techniques": sorted(data["techniques"]),
        }
        for m, data in sorted(combined.items())
    ]


def get_technique_manifest_for_query(
    graph: nx.DiGraph,
    query: str,
    os_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Extract targeted techniques, tools, or CVEs for a query and generate a clean manifest."""
    hits = query_graph(graph, query)
    matched_tools = [
        t for t in hits.get("matched_tools", [])
        if str(t).lower().strip() not in {"impacket", "metasploit", "powershell", "bash", "python"}
    ]
    matched_cves = list(hits.get("matched_cves", []))
    matched_techs = [
        t for t in hits.get("matched_techniques", [])
        if str(t).lower().strip() not in GENERIC_TECHNIQUES
    ]
    # If specific techniques or CVEs are matched, prioritize them over tool suites
    targets = (matched_cves + matched_techs) if (matched_cves or matched_techs) else matched_tools
    return generate_technique_manifest(graph, targets, os_filter=os_filter)
