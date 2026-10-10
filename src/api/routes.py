"""
routes.py – API endpoint handlers for the HTB RAG API.
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from src.api.schemas import QueryRequest, QueryResponse, RetrieveRequest
from src.pipeline.retriever import HybridRetriever
from src.pipeline.synthesizer import synthesize

logger = logging.getLogger(__name__)

router = APIRouter()

# Project root and static dir
project_root = Path(__file__).resolve().parent.parent.parent
static_dir = project_root / "static"

# Lazy retriever holder (configured/overridden by server)
_retriever_getter = None


def set_retriever_getter(getter_fn: Any) -> None:
    global _retriever_getter
    _retriever_getter = getter_fn


def _get_retriever() -> HybridRetriever:
    if _retriever_getter is not None:
        return _retriever_getter()
    from src.api.server import get_retriever
    return get_retriever()


@router.get("/", include_in_schema=False)
async def index():
    """Serve the interactive web dashboard."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        {"status": "ok", "message": "HTB RAG API is running. Visit /docs for Swagger UI."}
    )


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Retrieve context **and** synthesise a cited answer."""
    t_start = time.time()
    retriever: HybridRetriever = _get_retriever()

    t0 = time.time()
    retrieval: Any = await asyncio.to_thread(
        retriever.retrieve,
        query=req.question,
        top_k=req.top_k,
        os_filter=req.os,
        difficulty_filter=req.difficulty,
    )
    t_ret = time.time() - t0

    t1 = time.time()
    result: Any = await asyncio.to_thread(synthesize, req.question, retrieval)
    t_syn = time.time() - t1

    total_latency = round(time.time() - t_start, 2)
    logger.info(
        f"Query '{req.question[:30]}...' -> Retrieval={t_ret:.2f}s | Synthesis={t_syn:.2f}s | "
        f"Total={total_latency:.2f}s | Provider={result.get('provider', 'unknown')}"
    )

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        graph_used=result["graph_used"],
        query=req.question,
        provider=result.get("provider", "unknown"),
        latency_seconds=total_latency,
        chunks=retrieval.get("chunks", []),
        graph=retrieval.get("graph", {}),
    )


@router.get("/health")
async def health():
    """Liveness / readiness probe with index stats."""
    retriever: HybridRetriever = _get_retriever()
    stats = retriever.graph_store.get_stats()
    return {
        "status": "ok",
        "chunks_indexed": len(retriever.docs),
        "graph_nodes": stats.get("nodes", 0),
        "graph_edges": stats.get("edges", 0),
    }


@router.get("/debug_llm")
def debug_llm():
    from src.config import GEMINI_API_KEY, GROQ_API_KEY, GROQ_MODEL, OPENROUTER_MODEL
    return {
        "has_groq": bool(GROQ_API_KEY),
        "groq_model": GROQ_MODEL,
        "has_gemini": bool(GEMINI_API_KEY),
        "openrouter_model": OPENROUTER_MODEL,
    }


@router.get("/machines")
async def machines():
    """Sorted list of all machine node names in the knowledge graph."""
    retriever: HybridRetriever = _get_retriever()
    return retriever.graph_store.get_all_machines()


@router.get("/techniques")
async def techniques():
    """Sorted list of all technique node names in the knowledge graph."""
    retriever: HybridRetriever = _get_retriever()
    return retriever.graph_store.get_all_techniques()


@router.get("/machine/{machine_name}")
async def machine_detail(machine_name: str):
    """Return metadata, techniques, tools, and CVEs for a single machine."""
    retriever: HybridRetriever = _get_retriever()
    details = retriever.graph_store.get_machine_details(machine_name)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_name}' not found")
    return details


@router.post("/retrieve")
def retrieve_raw(req: RetrieveRequest):
    """Raw retrieval result (no synthesis) — useful for debug / eval."""
    retriever: HybridRetriever = _get_retriever()

    result = retriever.retrieve(
        query=req.question,
        top_k=req.top_k,
    )

    return result
