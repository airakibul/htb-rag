"""
synthesizer.py – Cited answer generation solely via OpenRouter LLM models.

Formats retrieved context, prepends graph findings when available, and
calls the OpenRouter chat API with a strict cybersecurity system prompt.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_FALLBACK_MODELS,
    OPENROUTER_MODEL,
)

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
_MAX_CONTEXT_CHARS = 10000
_MAX_CHUNK_CHARS   = 1200


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


# ═════════════════════════════════════════════════════════════════════════════
#  LLM Provider Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _clean_response(text: str) -> str:
    """Strip chain-of-thought artifacts, reasoning monologues, and repair unclosed markdown."""
    if not text:
        return ""

    cleaned = text

    # 1. Strip explicit <think>...</think> tags
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)

    # 2. Strip thinking process headers if a model leaks internal monologue
    if "Here's a thinking process:" in cleaned:
        m = re.search(r"\n(#+\s+|###?\s+Recon|###?\s+Foothold|[-*]\s+\*\*|[-*]\s+`|[A-Z][a-z]+:)", cleaned)
        if m:
            cleaned = cleaned[m.start():]

    # 3. Strip leading reasoning paragraphs like "We need to answer: ... Let's extract ..."
    if cleaned.lstrip().startswith("We need to answer:") or cleaned.lstrip().startswith("We must use only"):
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


def _call_openrouter(messages: Any) -> str | None:
    """Generate answer using OpenRouter API with free models and fallbacks."""
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_openrouter_key_here":
        return None
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
        client: Any = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
            timeout=30.0,
            max_retries=0,  # Fail fast on rate limits without wasting time on retries
            default_headers={
                "HTTP-Referer": "https://github.com/airakibul/htb-rag",
                "X-Title": "HTB-RAG-Assistant",
            },
        )
        models_to_try = [OPENROUTER_MODEL] + [m for m in OPENROUTER_FALLBACK_MODELS if m != OPENROUTER_MODEL]
        for model in models_to_try:
            try:
                logger.info(f"Synthesizing answer via OpenRouter ({model})...")
                response: Any = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=3500,
                    temperature=0.1,
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    cleaned = _clean_response(content.strip())
                    if cleaned:
                        return cleaned
            except Exception as exc:
                err_str = str(exc)
                logger.warning(f"OpenRouter model '{model}' failed: {err_str}")
                # Account-level daily limit exceeded across all free models: stop immediately
                if "free-models-per-day" in err_str:
                    logger.error("🛑 OpenRouter daily limit reached for free models (50 requests/day). Add credits or supply a fresh OPENROUTER_API_KEY in .env.")
                    break
                continue
    except Exception as exc:
        logger.warning(f"OpenRouter client error: {exc}")
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  Answer synthesis
# ═════════════════════════════════════════════════════════════════════════════

def synthesize(
    query: str,
    retrieval_result: dict[str, Any],
) -> dict[str, Any]:
    """Generate a cited answer from retrieved context solely via OpenRouter.

    Returns::

        {
            "answer":      str,
            "sources":     [sorted unique source names],
            "chunks_used": int,
            "graph_used":  bool,
        }
    """
    context = format_context(retrieval_result)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        },
    ]

    answer_text = (
        _call_openrouter(messages)
        or "Insufficient data or OpenRouter rate limit reached to generate the answer."
    )


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
    }
