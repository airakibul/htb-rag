"""
groq_provider.py – Groq LLM provider implementation.

Concrete adapter implementing LLMProvider for fast Groq chat completions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.config import GROQ_API_KEY, GROQ_MODEL
from src.domain.interfaces import LLMProvider

logger = logging.getLogger(__name__)


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


class GroqProvider(LLMProvider):
    """LLMProvider implementation using the Groq API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL
        self.timeout = timeout
        self._cooldown_until: float = 0.0

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1800,
        temperature: float = 0.1,
    ) -> str | None:
        if not self.api_key:
            return None

        import time

        if time.time() < self._cooldown_until:
            logger.info("Groq is in cooldown due to rate limit; skipping directly to fallback provider.")
            return None

        try:
            from groq import Groq

            client: Any = Groq(api_key=self.api_key, timeout=self.timeout, max_retries=0)
            logger.info(f"Synthesizing answer via Groq ({self.model})...")
            messages: Any = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            # Clamp max_tokens to 800 to avoid Groq OTPM (output tokens per minute) 1000 limit
            effective_tokens = min(max_tokens, 800)
            response: Any = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=effective_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                cleaned = clean_response(content.strip())
                if cleaned:
                    return cleaned
        except Exception as exc:
            err_msg = str(exc).lower()
            if "429" in err_msg or "rate limit" in err_msg or "tokens per day" in err_msg:
                self._cooldown_until = time.time() + 120.0
                logger.warning(
                    f"Groq rate limit exceeded ({exc}). Cooldown activated for 120s, falling back immediately."
                )
            else:
                logger.warning(
                    f"Groq generation failed, falling back to Gemini/OpenRouter: {exc}"
                )
        return None
