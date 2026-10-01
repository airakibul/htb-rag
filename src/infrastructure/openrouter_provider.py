"""
openrouter_provider.py – OpenRouter LLM provider implementation.

Concrete adapter implementing LLMProvider for OpenRouter API with
automatic fallback between free models.
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_FALLBACK_MODELS,
    OPENROUTER_MODEL,
)
from src.domain.interfaces import LLMProvider
from src.infrastructure.groq_provider import clean_response

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """LLMProvider implementation using OpenRouter."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OPENROUTER_BASE_URL,
        model: str = OPENROUTER_MODEL,
        fallback_models: list[str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = base_url
        self.model = model
        self.fallback_models = fallback_models or OPENROUTER_FALLBACK_MODELS
        self.timeout = timeout

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1800,
        temperature: float = 0.1,
    ) -> str | None:
        if not self.api_key or self.api_key == "your_openrouter_key_here":
            return None
        try:
            from openai import OpenAI

            client: Any = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=0,
                default_headers={
                    "HTTP-Referer": "https://github.com/airakibul/htb-rag",
                    "X-Title": "HTB-RAG-Assistant",
                },
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            models_to_try = [self.model] + [
                m for m in self.fallback_models if m != self.model
            ]
            for model in models_to_try:
                try:
                    logger.info(f"Synthesizing answer via OpenRouter ({model})...")
                    response: Any = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    content = response.choices[0].message.content
                    if content and content.strip():
                        cleaned = clean_response(content.strip())
                        if cleaned:
                            return cleaned
                except Exception as exc:
                    err_str = str(exc)
                    logger.warning(f"OpenRouter model '{model}' failed: {err_str}")
                    if "free-models-per-day" in err_str:
                        logger.error(
                            "🛑 OpenRouter daily limit reached for free models (50 requests/day). "
                            "Add credits or supply a fresh OPENROUTER_API_KEY in .env."
                        )
                        break
                    continue
        except Exception as exc:
            logger.warning(f"OpenRouter client error: {exc}")
        return None
