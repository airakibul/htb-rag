"""
synthesizer.py – Cited answer generation via Groq (llama-3.3-70b-versatile).

Formats retrieved context, prepends graph findings when available, and
calls the Groq chat API with a strict cybersecurity system prompt.
"""

from __future__ import annotations

from typing import Any

import groq

from src.config import GROQ_API_KEY, GROQ_LLM_MODEL

# ═════════════════════════════════════════════════════════════════════════════
#  System prompt
# ═════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are a cybersecurity analyst assistant specialized in offensive security.
Answer questions strictly from the provided HTB writeup excerpts.

Rules:
1. Use ONLY information from the provided context. Never use your training data.
2. After every technique or finding, cite the machine:
   Format: (seen on: MachineA, MachineB)
3. For cheatsheet questions, group by attack phase:
   Recon → Foothold → Lateral Movement → Privilege Escalation
4. If context lacks sufficient info, say:
   "Insufficient data in the retrieved writeups."
5. Never invent CVE numbers, tool flags, usernames, or machine names.
6. Use bullet points for cheatsheet answers. Be concise but complete.
"""

# ── Context size budget ──────────────────────────────────────────────────────
_MAX_CONTEXT_CHARS = 6000
_MAX_CHUNK_CHARS   = 800


# ═════════════════════════════════════════════════════════════════════════════
#  Context formatting
# ═════════════════════════════════════════════════════════════════════════════

def format_context(retrieval_result: dict[str, Any]) -> str:
    """Build a context string from retrieval results.

    * Prepends graph findings (techniques + machines) when available.
    * Appends each chunk truncated to ~800 chars.
    * Total output capped at ~6 000 chars.
    """
    parts: list[str] = []
    used = 0

    # ── Graph findings header ────────────────────────────────────────────
    graph = retrieval_result.get("graph", {})
    techniques = graph.get("matched_techniques", [])
    machines   = graph.get("relevant_machines", [])

    if techniques or machines:
        header = (
            "=== Graph Findings ===\n"
            f"Techniques: {', '.join(techniques)}\n"
            f"Observed on: {', '.join(machines)}\n"
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
#  Answer synthesis
# ═════════════════════════════════════════════════════════════════════════════

def synthesize(
    query: str,
    retrieval_result: dict[str, Any],
) -> dict[str, Any]:
    """Generate a cited answer from retrieved context via Groq.

    Returns::

        {
            "answer":      str,
            "sources":     [sorted unique source names],
            "chunks_used": int,
            "graph_used":  bool,
        }
    """
    context = format_context(retrieval_result)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        },
    ]

    client = groq.Groq(api_key=GROQ_API_KEY)
    response = None
    # 1. Primary Groq model (openai/gpt-oss-120b)
    try:
        response = client.chat.completions.create(
            model=GROQ_LLM_MODEL,
            messages=messages,
            max_tokens=3000,
            temperature=0.1,
        )
    except Exception as exc:
        if "429" in str(exc) or "rate" in str(exc).lower() or "limit" in str(exc).lower():
            # 2. Secondary Groq model with separate quota (openai/gpt-oss-20b)
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=messages,
                    max_tokens=2500,
                    temperature=0.1,
                )
            except Exception:
                # 3. Ultimate fallback: Gemini Flash
                try:
                    import google.generativeai as genai
                    from src.config import GEMINI_API_KEY
                    genai.configure(api_key=GEMINI_API_KEY)
                    gemini_model = genai.GenerativeModel(
                        model_name="models/gemini-flash-latest",
                        system_instruction=SYSTEM_PROMPT,
                    )
                    g_resp = gemini_model.generate_content(
                        f"Context:\n{context}\n\nQuestion: {query}",
                        generation_config={"temperature": 0.1, "max_output_tokens": 3000},
                    )
                    answer_text = g_resp.text.strip()
                    chunks = retrieval_result.get("chunks", [])
                    sources = sorted({c.get("metadata", {}).get("source", "") for c in chunks if c.get("metadata", {}).get("source")})
                    graph = retrieval_result.get("graph", {})
                    graph_used = bool(graph.get("matched_techniques") or graph.get("relevant_machines"))
                    return {
                        "answer": answer_text,
                        "sources": sources,
                        "chunks_used": len(chunks),
                        "graph_used": graph_used,
                    }
                except Exception as final_exc:
                    raise final_exc from exc
        else:
            raise

    answer_text = response.choices[0].message.content.strip()

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
