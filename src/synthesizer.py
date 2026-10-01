"""Backward-compatible shim — delegates to src.pipeline.synthesizer and infrastructure providers."""

from src.infrastructure.gemini_provider import GeminiProvider
from src.infrastructure.groq_provider import GroqProvider
from src.infrastructure.openrouter_provider import OpenRouterProvider
from src.pipeline.synthesizer import (  # noqa: F401
    SYSTEM_PROMPT,
    Synthesizer,
    _clean_response,
    format_context,
    synthesize,
)


def _call_groq(messages):
    provider = GroqProvider()
    sys_prompt = messages[0]["content"] if messages and messages[0].get("role") == "system" else SYSTEM_PROMPT
    user_prompt = messages[1]["content"] if len(messages) > 1 else ""
    return provider.generate(system_prompt=sys_prompt, user_prompt=user_prompt)


def _call_gemini(user_content):
    provider = GeminiProvider()
    return provider.generate(system_prompt=SYSTEM_PROMPT, user_prompt=user_content)


def _call_openrouter(messages):
    provider = OpenRouterProvider()
    sys_prompt = messages[0]["content"] if messages and messages[0].get("role") == "system" else SYSTEM_PROMPT
    user_prompt = messages[1]["content"] if len(messages) > 1 else ""
    return provider.generate(system_prompt=sys_prompt, user_prompt=user_prompt)


__all__ = [
    "SYSTEM_PROMPT",
    "Synthesizer",
    "_call_gemini",
    "_call_groq",
    "_call_openrouter",
    "_clean_response",
    "format_context",
    "synthesize",
]
