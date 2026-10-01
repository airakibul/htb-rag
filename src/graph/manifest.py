"""
manifest.py – Graph-Assisted Manifest Generator.

Extracts compact machine-technique metadata manifests from the knowledge graph
to inject into LLM context, boosting recall without context overflow.
"""

from __future__ import annotations

import logging
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
    "intended",
    "shortcut",
    "template injection",
    "server side template injection",
}


def generate_machine_manifest(
    graph: nx.DiGraph,
    technique_or_category: str,
) -> list[dict[str, Any]]:
    """Return a compact manifest for all machines demonstrating a technique/category.

    Parameters
    ----------
    graph : nx.DiGraph
        The HTB knowledge graph.
    technique_or_category : str
        Target technique name or domain category.

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
        techniques = sorted(
            t for t in graph.predecessors(matched_node)
            if graph.nodes[t].get("type") == "technique"
            and str(t).lower().strip() not in GENERIC_TECHNIQUES
        )
    elif node_type == "technique":
        techniques = [matched_node]
    else:
        tech_preds = [
            t for t in graph.predecessors(matched_node)
            if graph.nodes[t].get("type") == "technique"
        ]
        techniques = sorted(tech_preds) if tech_preds else [matched_node]

    # 3. For each technique, find all machine nodes connected via 'demonstrates' edges
    machine_map: dict[str, dict[str, Any]] = {}
    for tech in techniques:
        # Predecessors: machine -> technique
        for p in graph.predecessors(tech):
            if graph.nodes[p].get("type") != "machine":
                continue
            rel = str(graph.edges[p, tech].get("rel", ""))
            if "demonstrate" in rel or "use" in rel:
                m = p
                if m not in machine_map:
                    # 4. For each machine, extract OS (from 'os' edge successor) and difficulty (from node attrs)
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
                machine_map[m]["techniques"].add(tech)

        # Successors: technique -> machine (if any)
        for succ in graph.successors(tech):
            if graph.nodes[succ].get("type") != "machine":
                continue
            rel = str(graph.edges[tech, succ].get("rel", ""))
            if "demonstrate" in rel or "use" in rel:
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
                machine_map[m]["techniques"].add(tech)

    # 5. Build and return the manifest list, sorted by machine name
    # 6. Deduplicate machines that appear under multiple techniques
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

    # If ADCS is matched along with Active Directory, prioritize the more specific ADCS
    if "ADCS" in matched_categories and "Active Directory" in matched_categories:
        matched_categories = [c for c in matched_categories if c != "Active Directory"]

    # Target OS resolution
    low = query.lower()
    target_os = os_filter
    if not target_os:
        if "windows" in low and "linux" not in low:
            target_os = "windows"
        elif "linux" in low and "windows" not in low:
            target_os = "linux"
        elif "active directory" in low or "adcs" in low:
            target_os = "windows"

    combined: dict[str, dict[str, Any]] = {}

    if matched_categories:
        for cat in matched_categories:
            for entry in generate_machine_manifest(graph, cat):
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
    else:
        for tech in matched_techniques:
            if str(tech).lower().strip() in GENERIC_TECHNIQUES:
                continue
            for entry in generate_machine_manifest(graph, tech):
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
    """Return a compact manifest for all machines demonstrating any of the given techniques.

    Does NOT expand categories, preserving high precision for technique-listing queries.
    """
    combined: dict[str, dict[str, Any]] = {}
    for tech in techniques:
        # Check high-precision tool node alternatives
        if "sqlmap" in tech.lower() and "sqlmap" in graph:
            for p in graph.predecessors("sqlmap"):
                if graph.nodes[p].get("type") == "machine":
                    diff = str(graph.nodes[p].get("difficulty", "unknown") or "unknown")
                    os_val = "unknown"
                    for s in graph.successors(p):
                        if graph.edges[p, s].get("rel") == "os":
                            os_val = s
                            break
                    if os_val == "unknown":
                        os_val = str(graph.nodes[p].get("os", "unknown") or "unknown")
                    if os_filter and os_val not in (os_filter, "unknown"):
                        continue
                    if p not in combined:
                        combined[p] = {
                            "machine": p,
                            "os": os_val,
                            "difficulty": diff,
                            "techniques": {tech},
                        }
                    else:
                        combined[p]["techniques"].add(tech)
            continue

        if ("evil-winrm" in tech.lower() or "winrm" in tech.lower()) and ("evil-winrm" in graph or "winrm" in graph):
            for t in ["evil-winrm", "winrm"]:
                if t in graph:
                    for p in graph.predecessors(t):
                        if graph.nodes[p].get("type") == "machine":
                            diff = str(graph.nodes[p].get("difficulty", "unknown") or "unknown")
                            os_val = "unknown"
                            for s in graph.successors(p):
                                if graph.edges[p, s].get("rel") == "os":
                                    os_val = s
                                    break
                            if os_val == "unknown":
                                os_val = str(graph.nodes[p].get("os", "unknown") or "unknown")
                            if os_filter and os_val not in (os_filter, "unknown"):
                                continue
                            if p not in combined:
                                combined[p] = {
                                    "machine": p,
                                    "os": os_val,
                                    "difficulty": diff,
                                    "techniques": {tech},
                                }
                            else:
                                combined[p]["techniques"].add(tech)
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


GENERIC_CATEGORY_TECHNIQUES: set[str] = {
    "Active Directory Exploitation",
    "Windows Privilege Escalation",
    "Linux Privilege Escalation",
    "Password Cracking & Hash Dumping",
}


def get_technique_manifest_for_query(
    graph: nx.DiGraph,
    query: str,
    os_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Extract targeted techniques or tools for listing queries and generate a tight manifest.

    Prevents category-level over-expansion by matching directly to canonical techniques or
    specific tool nodes.
    """
    low = query.lower()

    # 1. High-precision tool nodes (sqlmap, evil-winrm)
    if "sqlmap" in low and "sqlmap" in graph:
        tool_machs = []
        for p in graph.predecessors("sqlmap"):
            if graph.nodes[p].get("type") == "machine":
                diff = str(graph.nodes[p].get("difficulty", "unknown") or "unknown")
                os_val = "unknown"
                for s in graph.successors(p):
                    if graph.edges[p, s].get("rel") == "os":
                        os_val = s
                        break
                if os_val == "unknown":
                    os_val = str(graph.nodes[p].get("os", "unknown") or "unknown")
                if os_filter and os_val not in (os_filter, "unknown"):
                    continue
                tool_machs.append({
                    "machine": p,
                    "os": os_val,
                    "difficulty": diff,
                    "techniques": ["SQL Injection with sqlmap"],
                })
        return sorted(tool_machs, key=lambda x: x["machine"])

    if ("evil-winrm" in low or "winrm" in low) and ("evil-winrm" in graph or "winrm" in graph):
        tool_machs_map: dict[str, dict[str, Any]] = {}
        for t in ["evil-winrm", "winrm"]:
            if t in graph:
                for p in graph.predecessors(t):
                    if graph.nodes[p].get("type") == "machine":
                        diff = str(graph.nodes[p].get("difficulty", "unknown") or "unknown")
                        os_val = "unknown"
                        for s in graph.successors(p):
                            if graph.edges[p, s].get("rel") == "os":
                                os_val = s
                                break
                        if os_val == "unknown":
                            os_val = str(graph.nodes[p].get("os", "unknown") or "unknown")
                        if os_filter and os_val not in (os_filter, "unknown"):
                            continue
                        if p not in tool_machs_map:
                            tool_machs_map[p] = {
                                "machine": p,
                                "os": os_val,
                                "difficulty": diff,
                                "techniques": {"WinRM Shell Access"},
                            }
                        else:
                            tool_machs_map[p]["techniques"].add("WinRM Shell Access")
        return [
            {
                "machine": m,
                "os": d["os"],
                "difficulty": d["difficulty"],
                "techniques": sorted(d["techniques"]),
            }
            for m, d in sorted(tool_machs_map.items())
        ]

    # 2. Match canonical techniques
    from src.graph.builder import CANONICAL_TECHNIQUES

    matched: list[str] = []
    for tech, info in CANONICAL_TECHNIQUES.items():
        patterns = info.get("patterns", [])
        fb_pats = info.get("fallback_patterns", [])
        fb_req = info.get("fallback_require", [])

        hit = False
        for p in patterns:
            if p in low:
                hit = True
                break
        if not hit and fb_pats and fb_req:
            if any(p in low for p in fb_pats) and any(r in low for r in fb_req):
                hit = True
        if hit and tech in graph:
            matched.append(tech)

    specific_matched = [t for t in matched if t not in GENERIC_CATEGORY_TECHNIQUES]
    chosen = specific_matched if specific_matched else matched

    return generate_technique_manifest(graph, chosen, os_filter=os_filter)

