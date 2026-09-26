"""
graph_builder.py – Enriched NetworkX knowledge graph for HTB writeups.

Node types : machine, technique, tool, cve, category, os, phase
Edge rels  : uses, demonstrates, exploits, belongs_to, enables, os, has_phase
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, cast

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001, S110
        pass

import networkx as nx
from networkx.readwrite import (  # type: ignore[import-untyped]
    node_link_data,
    node_link_graph,
)

from src.config import GRAPH_PATH

logger = logging.getLogger(__name__)

# ── Category keyword mapping ────────────────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "ADCS": (
        [f"esc{i}" for i in range(1, 17)]
        + [
            "certipy", "certify", "certificate", "adcs", "template",
            "certificate template", "ca enrollment",
        ]
    ),
    "Kerberos": [
        "as-rep", "asrep", "kerberoast", "kerberoasting", "rubeus",
        "silver ticket", "golden ticket", "tgt", "tgs", "kerberos",
        "getuserspns", "getnpusers", "kinit",
    ],
    "Active Directory": [
        "active directory", "ad", "domain controller", "domain admin",
        "bloodhound", "sharphound", "writeowner", "genericall", "writedacl",
        "genericwrite", "acl", "shadow credential", "dcsync", "secretsdump",
        "delegation", "rbcd", "unconstrained delegation", "constrained delegation",
        "gpo abuse", "ntds.dit", "kerberoast", "as-rep", "adcs",
    ],
    "Password Cracking": [
        "password cracking", "hash dumping", "hashcat", "john the ripper",
        "john", "secretsdump", "mimikatz", "hash dump", "dumping hashes",
        "ntds.dit", "sam dump", "cracking password", "hash",
    ],
    "Container Escape": [
        "docker", "docker.sock", "container", "escape", "breakout",
        "cgroup", "lxd", "runc", "container escape", "docker breakout",
    ],
    "Web": [
        "sqli", "sql injection", "xss", "ssrf", "lfi", "rfi",
        "injection", "burp", "sqlmap", "ssti", "nosql",
    ],
    "Linux-Privesc": [
        "linux privilege escalation", "linux privesc", "linux priv esc",
        "privilege escalation", "privesc",
        "sudo", "suid", "cron", "capabilities", "gtfobins", "dirtycow",
        "pwnkit", "no_root_squash", "path hijack", "cap_setuid",
    ],
    "Windows-Privesc": [
        "windows privilege escalation", "windows privesc", "windows priv esc",
        "privilege escalation", "privesc",
        "token", "potato", "juicypotato", "printspoofer", "godpotato",
        "uac", "alwaysinstallelevated", "seimpersonate", "unquoted service",
        "dll hijack", "sam hive", "system hive", "winpeas",
    ],
    "Network": [
        "smb", "samba", "ftp", "snmp", "rdp", "winrm", "evil-winrm",
        "ms17-010", "eternalblue", "sambacry", "cve-2007-2447",
    ],
}

# ── Canonical offensive techniques definitions ─────────────────────────────

CANONICAL_TECHNIQUES: dict[str, dict[str, Any]] = {
    # ── Windows Privilege Escalation ─────────────────────────────────────────
    "Token Impersonation (Potato / PrintSpoofer)": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": [
            "juicypotato", "printspoofer", "seimpersonate", "godpotato",
            "rottenpotato", "sweetpotato", "roguepotato", "badpotato", "efspotato",
        ],
    },
    "UAC Bypass": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": ["uac bypass", "cmstp", "fodhelper", "slui", "sdclt", "eventvwr"],
    },
    "AlwaysInstallElevated": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": ["alwaysinstallelevated"],
    },
    "Unquoted Service Path": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": ["unquoted service", "unquoted path", "trusted path"],
    },
    "DLL Hijacking": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": ["dll hijack", "dll side-load", "dll hijacking"],
    },
    "Insecure Service Permissions": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": ["service permission", "weak service", "sc config", "accesschk"],
    },
    "SAM / SYSTEM Hive Extraction": {
        "category": "Windows-Privesc",
        "secondary_category": "Password Cracking",
        "os": "windows",
        "patterns": ["sam hive", "system hive", "pwdump", "reg save hklm\\sam", "reg save hklm\\system"],
    },
    "Windows Privilege Escalation": {
        "category": "Windows-Privesc",
        "os": "windows",
        "patterns": ["winpeas", "powerup", "privilege escalation", "privesc"],
        "require_phase": "privesc",
    },

    # ── Linux Privilege Escalation ───────────────────────────────────────────
    "SUID / GTFOBins": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["suid", "gtfobins", "perm -4000", "setuid", "perm /4000"],
    },
    "Sudo Misconfiguration": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["sudo", "sudoers", "sudoedit", "sudo -l"],
    },
    "Cron Job Exploitation": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["cron", "crontab", "cronjob", "/etc/cron"],
    },
    "Linux Capabilities Abuse": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["getcap", "setcap", "cap_setuid", "capabilities"],
    },
    "Docker / Container Breakout": {
        "category": "Container Escape",
        "secondary_category": "Linux-Privesc",
        "patterns": [
            "docker.sock", "docker socket", "container breakout", "container escape",
            "docker breakout", "docker escape", "cgroup release_agent", "runc",
            "privileged container", "lxd escape", "lxd breakout",
        ],
    },
    "Linux Kernel Exploit": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["dirtycow", "pwnkit", "overlayfs", "cve-2016-5195", "cve-2021-4034"],
    },
    "NFS Root Squash Bypass": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["no_root_squash", "nfs share"],
    },
    "PATH Hijacking": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["path hijack", "path manipulation"],
    },
    "Linux Privilege Escalation": {
        "category": "Linux-Privesc",
        "os": "linux",
        "patterns": ["linpeas", "privilege escalation", "privesc"],
        "require_phase": "privesc",
    },

    # ── Active Directory ─────────────────────────────────────────────────────
    "AS-REP Roasting": {
        "category": "Active Directory",
        "secondary_category": "Kerberos",
        "os": "windows",
        "patterns": ["as-rep", "asrep", "getnpusers", "dont_req_preauth", "18200"],
    },
    "Kerberoasting": {
        "category": "Active Directory",
        "secondary_category": "Kerberos",
        "os": "windows",
        "patterns": ["kerberoast", "kerberoasting", "getuserspns", "spn", "13100"],
    },
    "DCSync Attack": {
        "category": "Active Directory",
        "secondary_category": "Password Cracking",
        "os": "windows",
        "patterns": ["dcsync", "ds-replication", "getncchanges", "drsuapi"],
    },
    "ADCS Certificate Abuse": {
        "category": "Active Directory",
        "secondary_category": "ADCS",
        "os": "windows",
        "patterns": [
            "adcs", "certipy", "certify", "certificate template",
            "esc1", "esc2", "esc3", "esc4", "esc5", "esc6", "esc7", "esc8", "esc9",
            "esc10", "esc11", "esc12", "esc13", "esc14", "esc15", "esc16",
        ],
    },
    "BloodHound Attack Path Analysis": {
        "category": "Active Directory",
        "os": "windows",
        "patterns": ["bloodhound", "sharphound", "attack path"],
    },
    "Shadow Credentials": {
        "category": "Active Directory",
        "os": "windows",
        "patterns": ["shadow credential", "pywhisker", "whisker", "msds-keycredentiallink"],
    },
    "ACL Abuse (GenericAll / WriteDACL / WriteOwner)": {
        "category": "Active Directory",
        "os": "windows",
        "patterns": ["genericall", "writedacl", "writeowner", "genericwrite", "set-domainobjectowner", "powerview"],
    },
    "Delegation Abuse (Unconstrained / Constrained / RBCD)": {
        "category": "Active Directory",
        "os": "windows",
        "patterns": [
            "rbcd", "resource-based constrained delegation", "unconstrained delegation",
            "constrained delegation", "s4u2self", "s4u2proxy",
        ],
    },
    "Active Directory Exploitation": {
        "category": "Active Directory",
        "os": "windows",
        "patterns": ["active directory", "domain controller", "domain admin", "ntds.dit", "sysvol"],
    },

    # ── Password Cracking & Credential Dumping ───────────────────────────────
    "Password Cracking & Hash Dumping": {
        "category": "Password Cracking",
        "patterns": [
            "secretsdump", "mimikatz", "hashcat", "john the ripper", "john",
            "hash dump", "dumping hashes", "ntds.dit", "sam dump", "cracking password",
        ],
    },

    # ── Specific Vulnerabilities & Web/Network Attacks ───────────────────────
    "SQL Injection with sqlmap": {
        "category": "Web",
        "patterns": ["sqlmap", "sqli", "sql injection"],
    },
    "CVE-2021-44228 Log4Shell": {
        "category": "Web",
        "patterns": ["log4j", "log4shell", "cve-2021-44228", "jndi:ldap", "marshalsec"],
    },
    "MS17-010 EternalBlue": {
        "category": "Network",
        "patterns": ["ms17-010", "eternalblue", "cve-2017-0143", "smb-vuln-ms17-010", "zzz_exploit"],
    },
    "Samba Remote Code Execution": {
        "category": "Network",
        "patterns": ["cve-2007-2447", "usermap_script", "sambacry", "cve-2017-7494"],
        "fallback_patterns": ["samba", "smbd"],
        "fallback_require": ["exploit", "rce", "remote code"],
    },
    "WinRM Shell Access": {
        "category": "Network",
        "patterns": ["evil-winrm", "winrm", "5985", "5986"],
    },
}

# Mapping known tools to their primary security categories
TOOL_CATEGORIES: dict[str, str] = {
    "bloodhound": "Active Directory",
    "sharphound": "Active Directory",
    "certipy": "ADCS",
    "certify": "ADCS",
    "rubeus": "Kerberos",
    "kerbrute": "Kerberos",
    "evil-winrm": "Network",
    "sqlmap": "Web",
    "hashcat": "Password Cracking",
    "john": "Password Cracking",
    "secretsdump": "Active Directory",
    "impacket": "Active Directory",
    "crackmapexec": "Active Directory",
    "netexec": "Active Directory",
    "linpeas": "Linux-Privesc",
    "winpeas": "Windows-Privesc",
}

# ── Curated aliases for CVE and Tool nodes ──────────────────────────────────

KNOWN_CVE_ALIASES: dict[str, list[str]] = {
    "CVE-2017-0143": ["ms17-010", "eternalblue", "smb-vuln-ms17-010"],
    "CVE-2021-44228": ["log4shell", "log4j", "jndi:ldap", "marshalsec"],
    "CVE-2007-2447": ["usermap_script", "samba rce", "sambacry"],
    "CVE-2017-7494": ["sambacry", "samba rce"],
    "CVE-2021-4034": ["pwnkit"],
    "CVE-2016-5195": ["dirtycow"],
    "CVE-2014-6271": ["shellshock"],
    "CVE-2019-14287": ["sudo bypass"],
}

KNOWN_TOOL_ALIASES: dict[str, list[str]] = {
    "printspoofer": ["seimpersonate", "spoolss"],
    "juicypotato": ["seimpersonate", "clsid", "potato"],
    "godpotato": ["seimpersonate", "potato"],
    "sweetpotato": ["seimpersonate", "potato"],
    "roguepotato": ["seimpersonate", "potato"],
    "certipy": ["adcs", "esc1", "esc8", "esc9", "certificate template"],
    "certify": ["adcs", "certificate template"],
    "rubeus": ["kerberos", "kerberoast", "as-rep", "tgt", "tgs"],
    "getnpusers": ["as-rep", "asrep", "roasting", "dont_req_preauth"],
    "getuserspns": ["kerberoast", "kerberoasting", "spn"],
    "secretsdump": ["dcsync", "ntds.dit", "hash dump", "sam dump"],
    "mimikatz": ["sekurlsa", "logonpasswords", "hash dump", "lsass"],
    "evil-winrm": ["winrm", "remote management users", "5985", "5986"],
    "sqlmap": ["sqli", "sql injection", "--os-shell"],
    "sharphound": ["bloodhound", "attack path"],
    "bloodhound": ["sharphound", "attack path"],
    "hashcat": ["password cracking", "hash dump"],
    "john": ["john the ripper", "password cracking"],
    "pywhisker": ["shadow credential", "msds-keycredentiallink"],
    "whisker": ["shadow credential", "msds-keycredentiallink"],
    "linpeas": ["privilege escalation", "privesc"],
    "winpeas": ["privilege escalation", "privesc"],
}

# ── Technique heading keywords (for raw heading extraction) ─────────────────

TECHNIQUE_KEYWORDS: list[str] = [
    "roast", "injection", "abuse", "exploit", "hijack", "spoof",
    "poisoning", "relay", "bypass", "escalat", "dump", "forge",
    "steal", "shadow", "privesc", "overflow", "traversal", "breakout",
    "gtfobins", "dcsync", "suid", "eternalblue", "log4shell",
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
        if cat == "Linux-Privesc" and os_val == "windows":
            continue
        if cat == "Windows-Privesc" and os_val == "linux":
            continue
        if any(kw in search for kw in keywords):
            cats.append(cat)
    return cats


# ═════════════════════════════════════════════════════════════════════════════
#  Graph construction
# ═════════════════════════════════════════════════════════════════════════════

def build_graph(all_chunks: list[dict[str, Any]]) -> nx.DiGraph:
    """Build a comprehensive knowledge graph from chunk metadata and content.

    Nodes created:
    - machine: each source writeup
    - os: target operating system (windows, linux)
    - category: broad domain categories
    - technique: canonical & heading techniques
    - tool: offensive tools used
    - cve: CVE identifiers
    - phase: attack phases (privesc, foothold, recon, etc.)

    Edges created:
    - machine → os (rel="os")
    - machine → tool (rel="uses")
    - machine → cve (rel="exploits")
    - machine → technique (rel="uses", rel="demonstrates")
    - machine → phase (rel="has_phase")
    - technique → category (rel="belongs_to")
    - technique → cve (rel="exploits")
    - tool → category (rel="belongs_to")
    - tool → technique (rel="enables")
    """
    G = nx.DiGraph()
    seen_os: dict[str, str] = {}

    for chunk in all_chunks:
        source = chunk.get("source", "")
        if not source:
            continue

        os_val = chunk.get("os", "unknown")
        h2 = chunk.get("h2", "")
        h3 = chunk.get("h3", "")
        breadcrumb = chunk.get("breadcrumb", "")
        phase = chunk.get("attack_phase", "")
        text = chunk.get("text", "")
        tools = _as_list(chunk.get("tools_mentioned", ""))
        cves = _as_list(chunk.get("cve_ids", ""))

        text_lower = text.lower()
        bc_lower = breadcrumb.lower()
        search_ctx = f"{bc_lower} {text_lower}"

        # ── Machine node ─────────────────────────────────────────────────
        if source not in G:
            G.add_node(source, type="machine")

        # ── OS node & edge ───────────────────────────────────────────────
        if os_val not in ("unknown", "") and source not in seen_os:
            if os_val not in G:
                G.add_node(os_val, type="os")
            G.add_edge(source, os_val, rel="os")
            seen_os[source] = os_val

        # ── Attack phase node & edge ─────────────────────────────────────
        if phase and phase not in ("unknown", ""):
            if phase not in G:
                G.add_node(phase, type="phase")
            if not G.has_edge(source, phase):
                G.add_edge(source, phase, rel="has_phase")

        # ── CVE nodes & edges (Direct machine → CVE) ─────────────────────
        for cve in cves:
            cve_up = cve.upper()
            cve_aliases = KNOWN_CVE_ALIASES.get(cve_up, [])
            if cve_up not in G:
                G.add_node(cve_up, type="cve", aliases=cve_aliases)
            else:
                existing = G.nodes[cve_up].get("aliases", [])
                if cve_aliases:
                    G.nodes[cve_up]["aliases"] = sorted(set(existing + cve_aliases))
            if not G.has_edge(source, cve_up):
                G.add_edge(source, cve_up, rel="exploits")

        # ── Tool nodes & edges ───────────────────────────────────────────
        for tool in tools:
            tool_clean = tool.lower().strip()
            tool_aliases = KNOWN_TOOL_ALIASES.get(tool_clean, [])
            if tool_clean not in G:
                G.add_node(tool_clean, type="tool", aliases=tool_aliases)
            else:
                existing = G.nodes[tool_clean].get("aliases", [])
                if tool_aliases:
                    G.nodes[tool_clean]["aliases"] = sorted(set(existing + tool_aliases))
            if not G.has_edge(source, tool_clean):
                G.add_edge(source, tool_clean, rel="uses")

            # Link tool to category if known
            if tool_clean in TOOL_CATEGORIES:
                tcat = TOOL_CATEGORIES[tool_clean]
                if tcat not in G:
                    G.add_node(tcat, type="category", aliases=CATEGORY_KEYWORDS.get(tcat, []))
                if not G.has_edge(tool_clean, tcat):
                    G.add_edge(tool_clean, tcat, rel="belongs_to")

        # ── Canonical Techniques Matching ────────────────────────────────
        for tech_name, tech_cfg in CANONICAL_TECHNIQUES.items():
            req_os = tech_cfg.get("os")
            if req_os and os_val != req_os:
                continue

            req_phase = tech_cfg.get("require_phase")
            if req_phase and phase != req_phase and req_phase not in bc_lower:
                continue

            patterns = tech_cfg.get("patterns", [])
            hit = any(pat in search_ctx for pat in patterns)

            # Fallback pattern check (e.g. for Samba RCE)
            if not hit and "fallback_patterns" in tech_cfg:
                has_fallback = any(fb in search_ctx for fb in tech_cfg["fallback_patterns"])
                has_req = any(rq in search_ctx for rq in tech_cfg.get("fallback_require", []))
                hit = has_fallback and has_req

            if hit:
                tech_patterns = tech_cfg.get("patterns", [])
                tech_fallbacks = tech_cfg.get("fallback_patterns", [])
                tech_aliases = sorted(set(tech_patterns + tech_fallbacks))
                if tech_name not in G:
                    G.add_node(tech_name, type="technique", aliases=tech_aliases)
                else:
                    existing = G.nodes[tech_name].get("aliases", [])
                    G.nodes[tech_name]["aliases"] = sorted(set(existing + tech_aliases))
                if not G.has_edge(source, tech_name):
                    # DiGraph allows only one edge per (src, dst); use combined rel
                    G.add_edge(source, tech_name, rel="uses_and_demonstrates")

                # Connect technique to category
                cat = tech_cfg.get("category")
                if cat:
                    if cat not in G:
                        G.add_node(cat, type="category", aliases=CATEGORY_KEYWORDS.get(cat, []))
                    if not G.has_edge(tech_name, cat):
                        G.add_edge(tech_name, cat, rel="belongs_to")

                sec_cat = tech_cfg.get("secondary_category")
                if sec_cat:
                    if sec_cat not in G:
                        G.add_node(sec_cat, type="category", aliases=CATEGORY_KEYWORDS.get(sec_cat, []))
                    if not G.has_edge(tech_name, sec_cat):
                        G.add_edge(tech_name, sec_cat, rel="belongs_to")

                # Link relevant tools to technique
                for tool in tools:
                    t_clean = tool.lower().strip()
                    if (t_clean in patterns or any(t_clean in p for p in patterns)) and not G.has_edge(t_clean, tech_name):
                        G.add_edge(t_clean, tech_name, rel="enables")

                # Link CVEs to technique
                for cve in cves:
                    cve_up = cve.upper()
                    if not G.has_edge(tech_name, cve_up):
                        G.add_edge(tech_name, cve_up, rel="exploits")

        # ── Heading-based technique extraction (h3 or h2) ────────────────
        target_heading = h3 if (h3 and _is_technique(h3)) else (h2 if (h2 and _is_technique(h2)) else "")
        if target_heading:
            clean_head = re.sub(r"^(privesc\s*#?\d*|exploit\s*#?\d*)\s*[-:]\s*", "", target_heading, flags=re.IGNORECASE).strip()
            if not clean_head:
                clean_head = target_heading.strip()

            if clean_head not in G:
                G.add_node(clean_head, type="technique", aliases=[clean_head.lower()])
            if not G.has_edge(source, clean_head):
                G.add_edge(source, clean_head, rel="uses")

            # technique → exploits → cve
            for cve in cves:
                cve_up = cve.upper()
                cve_aliases = KNOWN_CVE_ALIASES.get(cve_up, [])
                if cve_up not in G:
                    G.add_node(cve_up, type="cve", aliases=cve_aliases)
                else:
                    existing = G.nodes[cve_up].get("aliases", [])
                    if cve_aliases:
                        G.nodes[cve_up]["aliases"] = sorted(set(existing + cve_aliases))
                if not G.has_edge(clean_head, cve_up):
                    G.add_edge(clean_head, cve_up, rel="exploits")

            # technique → belongs_to → category
            for cat in _categorize(clean_head, h2, tools, os_val):
                if cat not in G:
                    G.add_node(cat, type="category", aliases=CATEGORY_KEYWORDS.get(cat, []))
                if not G.has_edge(clean_head, cat):
                    G.add_edge(clean_head, cat, rel="belongs_to")

    return G


# ═════════════════════════════════════════════════════════════════════════════
#  Persistence
# ═════════════════════════════════════════════════════════════════════════════

def save_graph(graph: nx.DiGraph) -> None:
    path = Path(GRAPH_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = node_link_data(graph)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info(
        f"🔗 Graph saved → {path}  "
        f"({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)"
    )


def load_graph() -> nx.DiGraph:
    path = Path(GRAPH_PATH)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return cast(nx.DiGraph, node_link_graph(data, directed=True))
    return nx.DiGraph()


# ═════════════════════════════════════════════════════════════════════════════
#  Query helpers
# ═════════════════════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════════════════════
#  Full query
# ═════════════════════════════════════════════════════════════════════════════

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


def main() -> None:
    """Rebuild and save the knowledge graph from ChromaDB documents."""
    from src import embedder

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.info("Reading chunks from ChromaDB...")
    all_stored = embedder.get_all_documents()
    if not all_stored:
        logger.warning("No documents found in ChromaDB. Ensure ingestion has been run.")
        return

    full_chunks = []
    for doc in all_stored:
        c = dict(doc.get("metadata", {}))
        c["text"] = doc.get("text", "")
        full_chunks.append(c)

    logger.info(f"Building knowledge graph from {len(full_chunks)} chunks...")
    graph = build_graph(full_chunks)
    save_graph(graph)

    n_mach = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "machine")
    n_tech = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "technique")
    n_cve = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "cve")
    n_tool = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "tool")
    n_cat = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "category")
    logger.info(
        f"✅ Successfully rebuilt graph with {graph.number_of_nodes()} nodes "
        f"({n_mach} machines, {n_tech} techniques, {n_cve} CVEs, {n_tool} tools, {n_cat} categories) "
        f"and {graph.number_of_edges()} edges."
    )


if __name__ == "__main__":
    main()

