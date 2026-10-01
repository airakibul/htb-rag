"""
synthesizer.py – Cited answer generation via pluggable LLMProvider fallback chain.

Follows SOLID Dependency Inversion principle by accepting a chain of LLMProvider
instances (Groq → Gemini → OpenRouter by default).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.domain.interfaces import LLMProvider
from src.infrastructure.gemini_provider import GeminiProvider
from src.infrastructure.groq_provider import GroqProvider, clean_response
from src.infrastructure.openrouter_provider import OpenRouterProvider

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
#  System prompt
# ═════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are a cybersecurity analyst assistant specialized in offensive security.
Answer questions strictly from the provided HTB writeup excerpts.

IMPORTANT:
- Output ONLY the final cheatsheet/answer directly in clean markdown.
- Do NOT output any internal thoughts, reasoning steps, or planning notes ('We need to...', 'Let\\'s analyze...', 'Thinking Process:'). Start immediately with the markdown answer.

Rules:
1. Use ONLY information from the provided context. Never use your training data.
2. After every technique or finding, cite the machine:
   Format: (seen on: MachineA, MachineB)
3. For cheatsheet questions, group by attack phase:
   Recon → Foothold → Lateral Movement → Privilege Escalation
4. If context lacks sufficient info, say:
   "Insufficient data in the retrieved writeups."
5. Never invent CVE numbers, tool flags, usernames, or machine names.
6. Use bullet points for cheatsheet answers with explicit tool commands in code blocks or inline backticks. Be concise but complete.
"""

# ── Context size budget ──────────────────────────────────────────────────────
_MAX_CONTEXT_CHARS = 18000   # Broad queries retrieve 25 chunks; modern LLMs handle 128K+
_MAX_CHUNK_CHARS   = 1500


# ═════════════════════════════════════════════════════════════════════════════
#  Context formatting
# ═════════════════════════════════════════════════════════════════════════════

def format_context(retrieval_result: dict[str, Any]) -> str:
    """Build a context string from retrieval results.

    * Prepends verified graph findings (technique → machines mapping) when available.
    * Appends each chunk truncated to ~1200 chars.
    * Total output capped at ~16 000 chars.
    """
    parts: list[str] = []
    used = 0

    # ── Graph findings header ────────────────────────────────────────────
    graph = retrieval_result.get("graph", {})
    tech_map = graph.get("technique_machines", {})
    techniques = graph.get("matched_techniques", [])
    machines   = graph.get("relevant_machines", [])

    if tech_map:
        header_lines = ["=== Graph Findings (Verified Techniques & Observed Machines) ==="]
        for tech, machs in list(tech_map.items())[:12]:
            mach_str = ", ".join(machs[:4])
            header_lines.append(f"- {tech} (seen on: {mach_str})")
        header_lines.append("===\n")
        header = "\n".join(header_lines)
        parts.append(header)
        used += len(header)
    elif techniques or machines:
        header = (
            "=== Graph Findings ===\n"
            f"Techniques: {', '.join(techniques[:15])}\n"
            f"Observed on: {', '.join(machines[:20])}\n"
            "===\n"
        )
        parts.append(header)
        used += len(header)

    # ── Chunk excerpts ───────────────────────────────────────────────────
    for chunk in retrieval_result.get("chunks", []):
        meta   = chunk.get("metadata", {})
        source = meta.get("source", "?")
        bc     = meta.get("breadcrumb", "")
        text   = chunk.get("text", "")[:_MAX_CHUNK_CHARS]

        block = (
            f"--- {source} | {bc} ---\n"
            f"{text}\n"
        )

        if used + len(block) > _MAX_CONTEXT_CHARS:
            break

        parts.append(block)
        used += len(block)

    return "\n".join(parts)


def _clean_response(text: str) -> str:
    """Backward-compatible alias for clean_response."""
    return clean_response(text)


# ═════════════════════════════════════════════════════════════════════════════
#  Synthesizer Class
# ═════════════════════════════════════════════════════════════════════════════

class Synthesizer:
    """Answer synthesizer supporting pluggable LLMProvider chains."""

    def __init__(
        self,
        providers: list[LLMProvider] | None = None,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self.system_prompt = system_prompt
        if providers is None:
            self.providers: list[LLMProvider] = [
                GroqProvider(),
                GeminiProvider(),
                OpenRouterProvider(),
            ]
        else:
            self.providers = providers

    def synthesize(
        self,
        query: str,
        retrieval_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a cited answer from retrieved context using the provider chain."""
        context = format_context(retrieval_result)
        user_prompt = f"Context:\n{context}\n\nQuestion: {query}"

        provider_name = "none"
        answer_text: str | None = None

        for p in self.providers:
            try:
                answer_text = p.generate(
                    system_prompt=self.system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=1800,
                    temperature=0.1,
                )
                if answer_text:
                    p_name = p.__class__.__name__.lower().replace("provider", "")
                    provider_name = p_name or "llm"
                    break
            except Exception as exc:
                logger.warning(f"Provider {p.__class__.__name__} failed: {exc}")
                continue

        if not answer_text:
            answer_text = "Insufficient data or LLM rate limit reached to generate the answer."

        logger.info(f"Synthesized answer using provider: {provider_name}")

        # ── Collect unique sources cited ─────────────────────────────────────
        chunks = retrieval_result.get("chunks", [])
        sources = sorted({
            c.get("metadata", {}).get("source", "")
            for c in chunks
            if c.get("metadata", {}).get("source")
        })

        # ── Graph usage flag ─────────────────────────────────────────────────
        graph = retrieval_result.get("graph", {})
        graph_used = bool(
            graph.get("matched_techniques")
            or graph.get("relevant_machines")
        )

        return {
            "answer":      answer_text,
            "sources":     sources,
            "chunks_used": len(chunks),
            "graph_used":  graph_used,
            "provider":    provider_name,
        }


# Module-level convenience function
def synthesize(
    query: str,
    retrieval_result: dict[str, Any],
    providers: list[LLMProvider] | None = None,
) -> dict[str, Any]:
    """Generate a cited answer from retrieved context via LLMProvider fallback chain."""
    return Synthesizer(providers=providers).synthesize(query, retrieval_result)
