"""
graph_builder.py – Build a NetworkX knowledge graph from chunk metadata.

Node types : machine, technique, tool, cve, category
Edge rels  : uses, exploits, belongs_to, os
"""

from __future__ import annotations

import pickle
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import networkx as nx

from src.config import GRAPH_PATH

# ── Category keyword mapping ────────────────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "ADCS": (
        [f"esc{i}" for i in range(1, 16)]
        + ["certipy", "certify", "certificate", "adcs", "template"]
    ),
    "Kerberos": [
        "as-rep", "kerberoast", "rubeus", "silver ticket",
        "tgt", "tgs", "kerberos",
    ],
    "AD": [
        "bloodhound", "writeowner", "genericall", "writedacl",
        "acl", "shadow credential",
    ],
    "Web": [
        "sqli", "xss", "ssrf", "lfi", "rfi",
        "injection", "burp", "sqlmap",
    ],
    "Linux-Privesc": ["sudo", "suid", "cron", "capabilities"],
    "Windows-Privesc": [
        "token", "potato", "printspoofer", "uac",
        "alwaysinstallelevated",
    ],
    "Network": ["smb", "samba", "ftp", "snmp", "rdp"],
}

# ── Technique heading keywords ──────────────────────────────────────────────

TECHNIQUE_KEYWORDS: list[str] = [
    "roast", "injection", "abuse", "exploit", "hijack", "spoof",
    "poisoning", "relay", "bypass", "escalat", "dump", "forge",
    "steal", "shadow", "privesc", "overflow", "traversal",
]

_CVE_RE = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _as_list(value: Any) -> list[str]:
    """Normalise a field that may be a comma-separated string **or** a list."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if v and str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def _is_technique(heading: str) -> bool:
    """Return *True* if *heading* contains a known technique keyword."""
    low = heading.lower()
    return any(kw in low for kw in TECHNIQUE_KEYWORDS)


def _categorize(
    technique: str, h2: str, tools: list[str], os_val: str,
) -> list[str]:
    """Determine which categories a technique belongs to."""
    search = f"{technique} {h2} {' '.join(tools)}".lower()
    cats: list[str] = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        # OS-gated categories
        if cat == "Linux-Privesc" and os_val != "linux":
            continue
        if cat == "Windows-Privesc" and os_val != "windows":
            continue
        if any(kw in search for kw in keywords):
            cats.append(cat)
    return cats


# ═════════════════════════════════════════════════════════════════════════════
#  Graph construction
# ═════════════════════════════════════════════════════════════════════════════

def build_graph(all_chunks: list[dict[str, Any]]) -> nx.DiGraph:
    """Build a knowledge graph from chunk metadata.

    Parameters
    ----------
    all_chunks : list[dict]
        Chunk dicts produced by the chunker (or retrieved from ChromaDB).

    Returns
    -------
    nx.DiGraph
        The populated knowledge graph.
    """
    G = nx.DiGraph()
    seen_os: dict[str, str] = {}           # machine → os (one edge each)

    for chunk in all_chunks:
        source = chunk.get("source", "")
        if not source:
            continue

        os_val = chunk.get("os", "unknown")
        h2     = chunk.get("h2", "")
        h3     = chunk.get("h3", "")
        tools  = _as_list(chunk.get("tools_mentioned", ""))
        cves   = _as_list(chunk.get("cve_ids", ""))

        # ── Machine node ─────────────────────────────────────────────────
        if source not in G:
            G.add_node(source, type="machine")

        # ── OS edge (one per machine) ────────────────────────────────────
        if os_val not in ("unknown", "") and source not in seen_os:
            if os_val not in G:
                G.add_node(os_val, type="os")
            G.add_edge(source, os_val, rel="os")
            seen_os[source] = os_val

        # ── Tool nodes & edges ───────────────────────────────────────────
        for tool in tools:
            if tool not in G:
                G.add_node(tool, type="tool")
            if not G.has_edge(source, tool):
                G.add_edge(source, tool, rel="uses")

        # ── Technique inference from h3 heading ──────────────────────────
        if h3 and _is_technique(h3):
            if h3 not in G:
                G.add_node(h3, type="technique")
            if not G.has_edge(source, h3):
                G.add_edge(source, h3, rel="uses")

            # technique → exploits → cve
            for cve in cves:
                cve_up = cve.upper()
                if cve_up not in G:
                    G.add_node(cve_up, type="cve")
                if not G.has_edge(h3, cve_up):
                    G.add_edge(h3, cve_up, rel="exploits")

            # technique → belongs_to → category
            for cat in _categorize(h3, h2, tools, os_val):
                if cat not in G:
                    G.add_node(cat, type="category")
                if not G.has_edge(h3, cat):
                    G.add_edge(h3, cat, rel="belongs_to")

    return G


# ═════════════════════════════════════════════════════════════════════════════
#  Persistence
# ═════════════════════════════════════════════════════════════════════════════

def save_graph(graph: nx.DiGraph) -> None:
    """Pickle the graph to :pydata:`GRAPH_PATH`."""
    path = Path(GRAPH_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(graph, f)
    print(
        f"🔗 Graph saved → {path}  "
        f"({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)"
    )


def load_graph() -> nx.DiGraph:
    """Load the graph from :pydata:`GRAPH_PATH`, or return an empty DiGraph."""
    path = Path(GRAPH_PATH)
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)                  # noqa: S301
    return nx.DiGraph()


# ═════════════════════════════════════════════════════════════════════════════
#  Query helpers
# ═════════════════════════════════════════════════════════════════════════════

def get_machines_for_technique(
    graph: nx.DiGraph, technique: str,
) -> list[str]:
    """Return machines that *use* the given technique."""
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
    """Return CVEs reachable from the machine (machine → technique → cve)."""
    if machine not in graph:
        return []
    cves: set[str] = set()
    for tech in graph.successors(machine):
        if graph.nodes[tech].get("type") != "technique":
            continue
        for target in graph.successors(tech):
            if graph.nodes[target].get("type") == "cve":
                cves.add(target)
    return sorted(cves)


# ═════════════════════════════════════════════════════════════════════════════
#  Full query
# ═════════════════════════════════════════════════════════════════════════════

def query_graph(
    graph: nx.DiGraph, query: str,
) -> dict[str, list[str]]:
    """Match a free-text *query* against the knowledge graph.

    Checks category keywords, tool node names, and CVE patterns.
    Returns a dict with five lists (all empty if nothing matched).
    """
    low = query.lower()

    # ── Categories ───────────────────────────────────────────────────────
    matched_categories: list[str] = [
        cat for cat, keywords in CATEGORY_KEYWORDS.items()
        if any(kw in low for kw in keywords)
    ]

    # ── Tools (tool nodes whose name appears in the query) ───────────────
    matched_tools: list[str] = sorted({
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "tool" and node in low
    })

    # ── CVEs ─────────────────────────────────────────────────────────────
    matched_cves: list[str] = sorted({
        c.upper() for c in _CVE_RE.findall(query) if c.upper() in graph
    })

    # ── Techniques (derived from matched categories) ─────────────────────
    matched_techniques: list[str] = sorted({
        tech
        for cat in matched_categories
        for tech in get_techniques_for_category(graph, cat)
    })

    # ── Relevant machines (reachable from any match) ─────────────────────
    machines: set[str] = set()

    for tech in matched_techniques:
        machines.update(get_machines_for_technique(graph, tech))

    for tool in matched_tools:
        machines.update(
            n for n in graph.predecessors(tool)
            if graph.nodes[n].get("type") == "machine"
        )

    for cve in matched_cves:
        for tech in graph.predecessors(cve):
            if graph.nodes[tech].get("type") == "technique":
                machines.update(get_machines_for_technique(graph, tech))

    return {
        "matched_categories": matched_categories,
        "matched_techniques": matched_techniques,
        "matched_tools":      matched_tools,
        "matched_cves":       matched_cves,
        "relevant_machines":  sorted(machines),
    }
