"""
query_enhancer.py – Dynamic query rewriting, expansion, and intent extraction.

Fuses fast LLM-based zero-shot intent analysis with Knowledge Graph aliasing,
with a robust offline fallback to ensure 100% reliability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import re
from typing import Any

import networkx as nx

from src.config import GROQ_API_KEY, GROQ_LLM_MODEL
from src.graph_builder import load_graph, query_graph

logger = logging.getLogger(__name__)

# Lightweight Groq client singleton
_groq_client: Any = None


def _get_groq_client() -> Any:
    global _groq_client
    if _groq_client is None and GROQ_API_KEY and GROQ_API_KEY != "your_groq_key_here":
        try:
            import groq
            _groq_client = groq.Groq(api_key=GROQ_API_KEY, timeout=5.0)
        except Exception as exc:
            logger.warning(f"Could not initialise Groq client for query enhancement: {exc}")
    return _groq_client


@dataclass
class EnhancedQuery:
    """Encapsulates dynamically parsed query signals."""
    query: str
    expanded_query: str
    expanded_terms: list[str] = field(default_factory=list)
    target_os: str | None = None          # "windows" | "linux" | None
    query_scope: str = "specific"         # "broad" | "specific"
    target_phase: str | None = None       # "recon" | "foothold" | "privesc" | None
    difficulty: str | None = None         # "easy" | "medium" | "hard" | "insane" | None


def _fallback_enhance(query: str, graph: nx.DiGraph | None = None) -> EnhancedQuery:
    """Robust offline intent extraction and graph-based expansion."""
    low = query.lower()

    # Scope detection
    broad_indicators = ["cheatsheet", "common", "across", "all machines", "overview", "list", "where"]
    query_scope = "broad" if any(w in low for w in broad_indicators) else "specific"

    # Phase detection
    target_phase = None
    if any(w in low for w in ["privilege escalation", "privesc", "root", "administrator", "system hive", "token impersonation"]):
        target_phase = "privesc"
    elif any(w in low for w in ["rce", "remote code", "exploit", "breakout", "escape", "foothold", "initial access", "shell"]):
        target_phase = "foothold"
    elif any(w in low for w in ["recon", "scan", "enumeration", "nmap", "discovery"]):
        target_phase = "recon"

    # OS detection
    target_os = None
    if "windows" in low and "linux" not in low:
        target_os = "windows"
    elif "linux" in low and "windows" not in low:
        target_os = "linux"

    # Difficulty detection
    difficulty = None
    for d in ("insane", "hard", "medium", "easy"):
        if re.search(rf"\b{d}\b", low):
            difficulty = d
            break

    # Graph-assisted extraction
    g = graph if graph is not None else load_graph()
    expanded_terms: list[str] = []

    if g is not None and g.number_of_nodes() > 0:
        hits = query_graph(g, query)

        # OS deduction from matched graph categories if OS wasn't explicitly stated
        if not target_os:
            cats = hits.get("matched_categories", [])
            if any(c in cats for c in ["Windows-Privesc", "Active Directory", "ADCS", "Kerberos"]):
                target_os = "windows"
            elif "Linux-Privesc" in cats:
                target_os = "linux"

        # Collect top aliases and names of matched nodes
        for cve in hits.get("matched_cves", [])[:3]:
            expanded_terms.append(cve)
            if cve in g:
                expanded_terms.extend(g.nodes[cve].get("aliases", [])[:2])
        for tool in hits.get("matched_tools", [])[:3]:
            expanded_terms.append(tool)
            if tool in g:
                expanded_terms.extend(g.nodes[tool].get("aliases", [])[:2])
        for tech in hits.get("matched_techniques", [])[:3]:
            if tech in g:
                expanded_terms.extend(g.nodes[tech].get("aliases", [])[:2])

    # Clean & deduplicate expanded terms
    clean_terms: list[str] = []
    seen = set(re.findall(r"\w+", low))
    for t in expanded_terms:
        tl = t.lower()
        if tl not in seen and len(tl) > 2:
            seen.add(tl)
            clean_terms.append(t)

    expanded_query = f"{query} {' '.join(clean_terms[:6])}".strip() if clean_terms else query

    return EnhancedQuery(
        query=query,
        expanded_query=expanded_query,
        expanded_terms=clean_terms[:6],
        target_os=target_os,
        query_scope=query_scope,
        target_phase=target_phase,
        difficulty=difficulty,
    )


def enhance_query(query: str, graph: nx.DiGraph | None = None) -> EnhancedQuery:
    """Enhance user query dynamically via fast LLM and Knowledge Graph signals.

    Returns an EnhancedQuery containing:
    - expanded_terms: synonyms, related tools, alternative CVEs
    - target_os: 'windows' | 'linux' | None
    - query_scope: 'broad' | 'specific'
    - target_phase: 'recon' | 'foothold' | 'privesc' | None
    - difficulty: 'easy' | 'medium' | 'hard' | 'insane' | None
    """
    client = _get_groq_client()
    if client is not None:
        system_msg = (
            "You are a cybersecurity expert. When given a query, respond with a single JSON object containing:\n"
            "- expanded_terms: list of 2-5 relevant security synonyms, alternative CVEs, or tools not in the query\n"
            "- target_os: \"windows\", \"linux\", or null. Only specify if strictly restricted to that OS (e.g. Windows tokens, AD). For cross-platform/Java (like Log4Shell), web exploits, or when not explicit, output null.\n"
            "- query_scope: \"broad\" for general OS-wide cheatsheets/overviews (e.g., all Windows privesc or all Linux privesc); \"specific\" for a particular CVE, vulnerability, tool, or single technique (e.g. Log4Shell, EternalBlue, sqlmap, Docker, JuicyPotato, Samba).\n"
            "- target_phase: \"recon\", \"foothold\", \"privesc\", or null\n"
            "- difficulty: \"easy\", \"medium\", \"hard\", \"insane\", or null"
        )
        prompt = f"Analyze query: {query}"

        # Try primary model then secondary
        models_to_try = [GROQ_LLM_MODEL, "openai/gpt-oss-20b"]
        for model_name in models_to_try:
            try:
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                    max_tokens=800,
                )
                raw_content = resp.choices[0].message.content or "{}"
                json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                if not json_match:
                    continue
                data = json.loads(json_match.group(0))

                # Normalise OS
                target_os = data.get("target_os")
                if target_os and isinstance(target_os, str):
                    target_os = target_os.lower()
                    if target_os not in ("windows", "linux"):
                        target_os = None

                # Normalise scope
                query_scope = data.get("query_scope", "specific")
                if query_scope not in ("broad", "specific"):
                    query_scope = "specific"

                # Normalise phase
                target_phase = data.get("target_phase")
                if target_phase and isinstance(target_phase, str):
                    target_phase = target_phase.lower()
                    if "priv" in target_phase:
                        target_phase = "privesc"
                    elif any(w in target_phase for w in ["foot", "exploit", "access", "rce", "breakout"]):
                        target_phase = "foothold"
                    elif "recon" in target_phase:
                        target_phase = "recon"
                    else:
                        target_phase = None

                # Normalise difficulty
                difficulty = data.get("difficulty")
                if difficulty and isinstance(difficulty, str):
                    difficulty = difficulty.lower()
                    if difficulty not in ("easy", "medium", "hard", "insane"):
                        difficulty = None

                llm_terms = data.get("expanded_terms", [])
                if not isinstance(llm_terms, list):
                    llm_terms = []

                # Enrich with Knowledge Graph signals
                g = graph if graph is not None else load_graph()
                graph_terms: list[str] = []
                if g is not None and g.number_of_nodes() > 0:
                    hits = query_graph(g, query)
                    if not target_os:
                        cats = hits.get("matched_categories", [])
                        if any(c in cats for c in ["Windows-Privesc", "Active Directory", "ADCS", "Kerberos"]):
                            target_os = "windows"
                        elif "Linux-Privesc" in cats:
                            target_os = "linux"

                    for cve in hits.get("matched_cves", [])[:2]:
                        graph_terms.append(cve)
                        if cve in g:
                            graph_terms.extend(g.nodes[cve].get("aliases", [])[:2])
                    for tool in hits.get("matched_tools", [])[:2]:
                        graph_terms.append(tool)
                        if tool in g:
                            graph_terms.extend(g.nodes[tool].get("aliases", [])[:2])

                # Deduplicate terms
                seen = set(re.findall(r"\w+", query.lower()))
                clean_terms: list[str] = []
                for t in (llm_terms + graph_terms):
                    if isinstance(t, str):
                        tl = t.lower()
                        if tl not in seen and len(tl) > 2:
                            seen.add(tl)
                            clean_terms.append(t)

                expanded_query = f"{query} {' '.join(clean_terms[:6])}".strip() if clean_terms else query

                return EnhancedQuery(
                    query=query,
                    expanded_query=expanded_query,
                    expanded_terms=clean_terms[:6],
                    target_os=target_os,
                    query_scope=query_scope,
                    target_phase=target_phase,
                    difficulty=difficulty,
                )

            except Exception as exc:
                logger.debug(f"LLM query enhancement attempt with {model_name} failed: {exc}")

    # Fallback when Groq is unavailable or failed
    return _fallback_enhance(query, graph)
