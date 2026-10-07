"""
schemas.py – Pydantic request and response schemas for HTB RAG API.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    top_k: int = 8
    os: str | None = None
    difficulty: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks_used: int
    graph_used: bool
    query: str
    provider: str = "unknown"
    latency_seconds: float = 0.0
    chunks: list[dict[str, Any]] = []
    graph: dict[str, Any] = {}


class RetrieveRequest(BaseModel):
    question: str
    top_k: int = 8
