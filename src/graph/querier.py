"""
querier.py – Graph query logic for HTB RAG knowledge graph.

Matches free-text queries against graph nodes (categories, techniques, tools, CVEs, machines)
and retrieves relational topology.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import networkx as nx

from src.graph.builder import (
    CANONICAL_TECHNIQUES,
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

    # ── Techniques (canonical pattern match, direct name match, or aliases) ───
    # ── Techniques (canonical pattern match, direct name match, or aliases) ───
    GENERIC_TECHNIQUES = {
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
    CATEGORY_LEVEL_TECHNIQUES = {
        "Active Directory Exploitation",
        "Windows Privilege Escalation",
        "Linux Privilege Escalation",
        "Password Cracking & Hash Dumping",
    }

    # 1. Canonical technique matches (highest precision)
    canonical_matches: list[str] = []
    for tech, info in CANONICAL_TECHNIQUES.items():
        patterns = info.get("patterns", [])
        fb_pats = info.get("fallback_patterns", [])
        fb_req = info.get("fallback_require", [])
        hit = any(p in low for p in patterns)
        if not hit and fb_pats and fb_req:
            if any(p in low for p in fb_pats) and any(r in low for r in fb_req):
                hit = True
        if hit and tech in graph:
            canonical_matches.append(tech)

    specific_canonical = [t for t in canonical_matches if t not in CATEGORY_LEVEL_TECHNIQUES]
    priority_techniques = specific_canonical if specific_canonical else canonical_matches

    # 2. Direct name or alias matches with word boundary check
    direct_techniques: list[str] = list(priority_techniques)
    for node, data in graph.nodes(data=True):
        if data.get("type") == "technique" and node not in direct_techniques:
            node_low = node.lower().strip()
            if node_low in GENERIC_TECHNIQUES or len(node_low) < 3:
                continue
            aliases = [a.lower().strip() for a in data.get("aliases", [])]
            matched = False
            if re.search(rf"\b{re.escape(node_low)}\b", low):
                matched = True
            elif any(re.search(rf"\b{re.escape(alias)}\b", low) for alias in aliases if len(alias) >= 3):
                matched = True
            if matched:
                direct_techniques.append(node)

    # Filter out umbrella category-level techniques if specific techniques exist
    if any(t not in CATEGORY_LEVEL_TECHNIQUES and t not in GENERIC_TECHNIQUES for t in direct_techniques):
        direct_techniques = [t for t in direct_techniques if t not in CATEGORY_LEVEL_TECHNIQUES and t.lower() not in GENERIC_TECHNIQUES]

    category_techniques = [
        tech
        for cat in matched_categories
        for tech in get_techniques_for_category(graph, cat)
        if tech not in direct_techniques and tech.lower() not in GENERIC_TECHNIQUES
    ]

    # 3. Category techniques (fallback for broad cheatsheets when no specific techniques are matched)
    if not direct_techniques and matched_categories:
        matched_techniques = sorted(category_techniques)
    else:
        matched_techniques = list(direct_techniques)

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
