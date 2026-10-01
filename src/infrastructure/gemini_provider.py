"""
gemini_provider.py – Gemini LLM provider implementation.

Concrete adapter implementing LLMProvider for Google Gemini API.
"""

from __future__ import annotations

import logging
from typing import Any

from src.config import GEMINI_API_KEY
from src.domain.interfaces import LLMProvider
from src.infrastructure.groq_provider import clean_response

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """LLMProvider implementation using Google Gemini."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-flash-latest",
    ) -> None:
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1800,
        temperature: float = 0.1,
    ) -> str | None:
        if not self.api_key or self.api_key == "your_gemini_key_here":
            return None
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
            )
            logger.info(f"Synthesizing answer via Gemini ({self.model_name})...")
            response = model.generate_content(
                user_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            if response.text and response.text.strip():
                cleaned = clean_response(response.text.strip())
                if cleaned:
                    return cleaned
        except Exception as exc:
            logger.warning(
                f"Gemini generation failed, falling back to OpenRouter: {exc}"
            )
        return None
