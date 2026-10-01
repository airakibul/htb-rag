"""
querier.py – Graph query logic for HTB RAG knowledge graph.

Matches free-text queries against graph nodes (categories, techniques, tools, CVEs, machines)
and retrieves relational topology.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from src.graph.builder import (
    CATEGORY_KEYWORDS,
    _CVE_RE,
)

logger = logging.getLogger(__name__)


def get_machines_for_technique(
    graph: nx.DiGraph, technique: str,
) -> list[str]:
    """Return machines that *use* or *demonstrate* the given technique."""
    if technique not in graph:
        return []
    return sorted(
        n for n in graph.predecessors(technique)
        if graph.nodes[n].get("type") == "machine"
    )


def get_techniques_for_category(
    graph: nx.DiGraph, category: str,
) -> list[str]:
    """Return techniques that *belong_to* the given category."""
    if category not in graph:
        return []
    return sorted(
        n for n in graph.predecessors(category)
        if graph.nodes[n].get("type") == "technique"
    )


def get_tools_for_machine(
    graph: nx.DiGraph, machine: str,
) -> list[str]:
    """Return tools that the given machine *uses*."""
    if machine not in graph:
        return []
    return sorted(
        n for n in graph.successors(machine)
        if graph.nodes[n].get("type") == "tool"
    )


def get_cves_for_machine(
    graph: nx.DiGraph, machine: str,
) -> list[str]:
    """Return CVEs reachable from the machine (direct or machine → technique → cve)."""
    if machine not in graph:
        return []
    cves: set[str] = set()
    for succ in graph.successors(machine):
        if graph.nodes[succ].get("type") == "cve":
            cves.add(succ)
        elif graph.nodes[succ].get("type") == "technique":
            for target in graph.successors(succ):
                if graph.nodes[target].get("type") == "cve":
                    cves.add(target)
    return sorted(cves)


def query_graph(
    graph: nx.DiGraph, query: str,
) -> dict[str, Any]:
    """Match a free-text *query* against the knowledge graph.

    Checks category keywords, canonical techniques, tool nodes, and CVE patterns.
    Returns a dict with:
    - matched_categories
    - matched_techniques
    - matched_tools
    - matched_cves
    - relevant_machines
    - technique_machines
    """
    low = query.lower()

    # ── Categories (matched by category name, node aliases, or CATEGORY_KEYWORDS) ─
    matched_categories: list[str] = sorted({
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "category" and (
            node.lower() in low
            or any(kw in low for kw in data.get("aliases", CATEGORY_KEYWORDS.get(node, [])))
        )
    })
    # Filter out opposite OS category if an explicit OS is mentioned
    if "windows" in low and "linux" not in low:
        matched_categories = [c for c in matched_categories if c != "Linux-Privesc"]
    elif "linux" in low and "windows" not in low:
        matched_categories = [c for c in matched_categories if c != "Windows-Privesc"]

    # ── Tools (matched by name or aliases) ───────────────────────────────
    matched_tools: list[str] = sorted({
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "tool" and (
            f" {node.lower()} " in f" {low} " or node.lower() == low
            or any(f" {alias.lower()} " in f" {low} " or alias.lower() == low for alias in data.get("aliases", []))
        )
    })

    # ── CVEs (matched by direct CVE regex, name, or aliases) ──────────────
    cve_regex_matches = {c.upper() for c in _CVE_RE.findall(query) if c.upper() in graph}
    cve_alias_matches = {
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "cve" and (
            node.lower() in low
            or any(alias.lower() in low for alias in data.get("aliases", []))
        )
    }
    matched_cves: list[str] = sorted(cve_regex_matches | cve_alias_matches)

    # ── Techniques (direct name match, word match, or aliases) ───────────
    direct_techniques: set[str] = set()
    for node, data in graph.nodes(data=True):
        if data.get("type") == "technique":
            node_low = node.lower()
            aliases = [a.lower() for a in data.get("aliases", [])]
            if (
                node_low in low
                or any(kw in low for kw in node_low.split() if len(kw) > 4)
                or any(alias in low for alias in aliases)
            ):
                direct_techniques.add(node)

    category_techniques: set[str] = {
        tech
        for cat in matched_categories
        for tech in get_techniques_for_category(graph, cat)
    }

    matched_techniques: list[str] = sorted(direct_techniques | category_techniques)

    # ── Relevant machines (reachable from matches) ───────────────────────
    machines: set[str] = set()

    # From direct or category techniques
    for tech in direct_techniques:
        machines.update(get_machines_for_technique(graph, tech))

    # From matched tools
    for tool in matched_tools:
        machines.update(
            n for n in graph.predecessors(tool)
            if graph.nodes[n].get("type") == "machine"
        )

    # From matched CVEs (both direct and via technique)
    for cve in matched_cves:
        machines.update(
            n for n in graph.predecessors(cve)
            if graph.nodes[n].get("type") == "machine"
        )
        for tech in graph.predecessors(cve):
            if graph.nodes[tech].get("type") == "technique":
                machines.update(get_machines_for_technique(graph, tech))

    # If machines set is empty or query is broad category query, expand from category techniques
    if not machines or any(w in low for w in ["cheatsheet", "common", "across", "all machines"]):
        for tech in category_techniques:
            machines.update(get_machines_for_technique(graph, tech))

    # Filter machines by OS if OS is explicitly in query
    if "windows" in low and "linux" not in low:
        machines = {
            m for m in machines
            if any(graph.edges[m, succ].get("rel") == "os" and succ == "windows" for succ in graph.successors(m))
        }
    elif "linux" in low and "windows" not in low:
        machines = {
            m for m in machines
            if any(graph.edges[m, succ].get("rel") == "os" and succ == "linux" for succ in graph.successors(m))
        }

    # Map matched techniques to machines that demonstrate them (with OS filtering)
    technique_machines: dict[str, list[str]] = {}
    for tech in matched_techniques:
        tech_machs = get_machines_for_technique(graph, tech)
        if "windows" in low and "linux" not in low:
            tech_machs = [
                m for m in tech_machs
                if any(graph.edges[m, succ].get("rel") == "os" and succ == "windows" for succ in graph.successors(m))
            ]
        elif "linux" in low and "windows" not in low:
            tech_machs = [
                m for m in tech_machs
                if any(graph.edges[m, succ].get("rel") == "os" and succ == "linux" for succ in graph.successors(m))
            ]
        if tech_machs:
            technique_machines[tech] = tech_machs[:6]

    return {
        "matched_categories": sorted(matched_categories),
        "matched_techniques": matched_techniques,
        "technique_machines": technique_machines,
        "matched_tools":      matched_tools,
        "matched_cves":       matched_cves,
        "relevant_machines":  sorted(machines),
    }
