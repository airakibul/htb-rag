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
from src.domain.models import RetrievalResult

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
4. For broad cheatsheet queries, if a "Complete Machine Manifest" table is provided:
   - Generate detailed exploit steps and commands from the retrieved chunk excerpts (cite machines).
   - Then synthesize comprehensive corpus coverage from the manifest table in an "## Also Demonstrated On" section.
   - Format: "Also demonstrated on: MachineA, MachineB, MachineC (technique-name)"
   - This ensures comprehensive corpus coverage in the final answer.
5. If context lacks sufficient info, say:
   "Insufficient data in the retrieved writeups."
6. Never invent CVE numbers, tool flags, usernames, or machine names.
7. Use bullet points for cheatsheet answers with explicit tool commands in code blocks or inline backticks. Be concise but complete.
"""

# ── Context size budget ──────────────────────────────────────────────────────
_MAX_CONTEXT_CHARS = 5500    # Lean, fast ~1,200 token budget for sub-second synthesis
_MAX_CHUNK_CHARS   = 900     # Dense command and exploit step focus


def compress_context_chunk(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> str:
    """Intelligently compress retrieved chunk text to maximize informational density.

    - Strips long hex / base64 payloads to save context budget
    - Removes repetitive ASCII terminal dividers and blank lines
    - Ensures code fences remain balanced
    - Retains vital exploit commands, paths, and output banners
    """
    if not text:
        return ""

    # Strip long hex dumps (> 40 chars) while preserving MD5/NTLM (32 chars) hashes
    compressed = re.sub(r"\b[0-9a-fA-F]{40,}\b", "[hex data omitted]", text)
    # Strip standalone long base64 strings (>= 60 chars) without corrupting short tokens or flags
    compressed = re.sub(r"\b[A-Za-z0-9+/=]{60,}\b", "[base64 omitted]", compressed)
    # Collapse repetitive terminal dividers (e.g. ------ or ======)
    compressed = re.sub(r"[-=~_*]{5,}", "-----", compressed)
    # Collapse multiple blank lines
    compressed = re.sub(r"\n{3,}", "\n\n", compressed)

    if len(compressed) > max_chars:
        compressed = compressed[:max_chars].rstrip() + "\n... [truncated]"

    # Ensure unclosed code fences are properly terminated
    if compressed.count("```") % 2 != 0:
        compressed += "\n```"

    return compressed


# ═════════════════════════════════════════════════════════════════════════════
#  Context formatting
# ═════════════════════════════════════════════════════════════════════════════

def format_context(
    retrieval_result: dict[str, Any] | RetrievalResult,
    is_broad: bool | None = None,
) -> str:
    """Build a concise, high-density context string from retrieval results.

    * Injects 5-8 compressed chunk excerpts focusing on exact exploit steps.
    * Appends compact machine manifest table for full corpus coverage when available.
    * Capped strictly at ~5,500 characters (~1,200 tokens) to guarantee sub-second synthesis.
    """
    parts: list[str] = []
    used = 0

    chunks = (
        retrieval_result.chunks
        if isinstance(retrieval_result, RetrievalResult)
        else (retrieval_result.get("chunks", []) if hasattr(retrieval_result, "get") else [])
    )
    if is_broad is None:
        is_broad = len(chunks) > 5

    max_budget = 6500 if is_broad else _MAX_CONTEXT_CHARS

    manifest = (
        retrieval_result.manifest
        if isinstance(retrieval_result, RetrievalResult)
        else retrieval_result.get("manifest")
    )

    # ── Graph findings header (only if no manifest table to prevent duplication) ──
    if not manifest:
        graph = retrieval_result.get("graph", {})
        tech_map = graph.get("technique_machines", {})
        techniques = graph.get("matched_techniques", [])
        machines   = graph.get("relevant_machines", [])

        if tech_map:
            header_lines = ["=== Graph Findings (Verified Techniques & Observed Machines) ==="]
            for tech, machs in list(tech_map.items())[:6]:
                mach_str = ", ".join(machs[:3])
                header_lines.append(f"- {tech} (seen on: {mach_str})")
            header_lines.append("===\n")
            header = "\n".join(header_lines)
            parts.append(header)
            used += len(header)
        elif techniques or machines:
            header = (
                "=== Graph Findings ===\n"
                f"Techniques: {', '.join(techniques[:8])}\n"
                f"Observed on: {', '.join(machines[:10])}\n"
                "===\n"
            )
            parts.append(header)
            used += len(header)

    # ── Chunk excerpts with Context Compression ──
    for chunk in chunks:
        if isinstance(chunk, dict):
            meta: dict[str, Any] = chunk.get("metadata", {}) or {}
            raw_text: str = str(chunk.get("text", ""))
        else:
            meta = getattr(chunk, "metadata", {}) or {}
            raw_text = str(getattr(chunk, "text", ""))

        source = meta.get("source", "?")
        bc     = meta.get("breadcrumb", "")
        parent = meta.get("parent_path") or bc
        text   = compress_context_chunk(raw_text, max_chars=_MAX_CHUNK_CHARS)

        block = (
            f"--- {source} | {parent} ---\n"
            f"{text}\n"
        )

        if used + len(block) > max_budget:
            break

        parts.append(block)
        used += len(block)

    # ── Manifest Table Injection (Compact ~200-300 tokens) ──
    if manifest:
        manifest_lines = ["=== Complete Machine Manifest (Graph-Verified) ==="]
        manifest_lines.append("| Machine | OS | Techniques |")
        manifest_lines.append("|---------|-----|-----------|")
        for entry in manifest[:30]:  # Up to 30 machines gives wide coverage in ~180 tokens
            techs = ", ".join(entry.get("techniques", [])[:2])
            manifest_lines.append(f"| {entry['machine']} | {entry.get('os', '?')} | {techs} |")
        manifest_lines.append("===\n")
        manifest_block = "\n".join(manifest_lines)

        if used + len(manifest_block) < max_budget + 1500:
            parts.append(manifest_block)
            used += len(manifest_block)

    return "\n".join(parts)


def clean_response(text: str) -> str:
    """Strip chain-of-thought artifacts, reasoning monologues, and repair unclosed markdown."""
    if not text:
        return ""

    cleaned = text

    # 1. Strip explicit <think>...</think> tags
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)

    # 2. Strip thinking process headers if a model leaks internal monologue
    if "Here's a thinking process:" in cleaned:
        m = re.search(
            r"\n(#+\s+|###?\s+Recon|###?\s+Foothold|[-*]\s+\*\*|[-*]\s+`|[A-Z][a-z]+:)",
            cleaned,
        )
        if m:
            cleaned = cleaned[m.start():]

    # 3. Strip leading reasoning paragraphs like "We need to answer: ... Let's extract ..."
    if cleaned.lstrip().startswith("We need to answer:") or cleaned.lstrip().startswith(
        "We must use only"
    ):
        m = re.search(r"\n(#+\s+|Recon\b|Foothold\b|[-*]\s+)", cleaned)
        if m:
            cleaned = cleaned[m.start():]

    cleaned = cleaned.strip()

    # 4. Repair unclosed multi-line code fences ```
    if cleaned.count("```") % 2 != 0:
        cleaned += "\n```"

    # 5. Repair unclosed inline code backticks `
    if cleaned.count("`") % 2 != 0:
        cleaned += "`"

    return cleaned


def _clean_response(text: str) -> str:
    """Backward-compatible alias for clean_response."""
    return clean_response(text)


def _default_providers() -> list[LLMProvider]:
    """Lazy fallback creating default provider chain."""
    from src.infrastructure.groq_provider import GroqProvider
    from src.infrastructure.openrouter_provider import OpenRouterProvider
    from src.infrastructure.gemini_provider import GeminiProvider
    return [
        GroqProvider(),
        OpenRouterProvider(),
        GeminiProvider(),
    ]


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
        self.providers: list[LLMProvider] = (
            providers if providers is not None else _default_providers()
        )

    def synthesize(
        self,
        query: str,
        retrieval_result: dict[str, Any] | RetrievalResult,
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

        # ── Collect genuine sources cited / used ──────────────────────────────
        # Sources from retrieved chunks provided to the LLM (zero fake manifest sources)
        chunks = (
            retrieval_result.chunks
            if isinstance(retrieval_result, RetrievalResult)
            else (retrieval_result.get("chunks", []) if hasattr(retrieval_result, "get") else [])
        )
        chunk_sources: set[str] = set()
        for c in chunks:
            if isinstance(c, dict):
                src = c.get("metadata", {}).get("source", "")
            else:
                src = getattr(c, "metadata", {}).get("source", "")
            if src:
                chunk_sources.add(str(src).lower())
        sources = sorted(s for s in chunk_sources if s)

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
    retrieval_result: dict[str, Any] | RetrievalResult,
    providers: list[LLMProvider] | None = None,
) -> dict[str, Any]:
    """Generate a cited answer from retrieved context via LLMProvider fallback chain."""
    return Synthesizer(providers=providers).synthesize(query, retrieval_result)
