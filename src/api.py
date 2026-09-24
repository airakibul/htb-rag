"""
api.py – FastAPI server exposing the HTB RAG pipeline.

Run::

    uvicorn src.api:app --reload --port 8000
"""

import sys
from pathlib import Path

# Add project root to sys.path if missing
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.graph_builder import (
    get_cves_for_machine,
    get_tools_for_machine,
)
from src.retriever import HybridRetriever
from src.synthesizer import synthesize

# ═════════════════════════════════════════════════════════════════════════════
#  Pydantic models
# ═════════════════════════════════════════════════════════════════════════════


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


class RetrieveRequest(BaseModel):
    question: str
    top_k: int = 5


# ═════════════════════════════════════════════════════════════════════════════
#  App state (populated at startup via lifespan)
# ═════════════════════════════════════════════════════════════════════════════

_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Initialise the HybridRetriever singleton on startup."""
    retriever = HybridRetriever()

    if not retriever.docs:
        print("⚠️  No chunks indexed. Run: python -m src.ingest")

    _state["retriever"] = retriever
    yield
    _state.clear()


# ═════════════════════════════════════════════════════════════════════════════
#  FastAPI app
# ═════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="HTB RAG API",
    description="Hybrid RAG over HackTheBox writeups",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global error handler ────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def _global_error(request: Request, exc: Exception):  # noqa: ARG001
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# ═════════════════════════════════════════════════════════════════════════════
#  Endpoints
# ═════════════════════════════════════════════════════════════════════════════


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Retrieve context **and** synthesise a cited answer."""
    retriever: HybridRetriever = _state["retriever"]

    retrieval = retriever.retrieve(
        query=req.question,
        top_k=req.top_k,
        os_filter=req.os,
        difficulty_filter=req.difficulty,
    )

    result = synthesize(req.question, retrieval)

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        graph_used=result["graph_used"],
        query=req.question,
    )


@app.get("/health")
async def health():
    """Liveness / readiness probe with index stats."""
    retriever: HybridRetriever = _state["retriever"]
    graph = retriever.graph
    return {
        "status": "ok",
        "chunks_indexed": len(retriever.docs),
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
    }


@app.get("/machines")
async def machines():
    """Sorted list of all machine node names in the knowledge graph."""
    retriever: HybridRetriever = _state["retriever"]
    graph = retriever.graph
    return sorted(
        n for n, d in graph.nodes(data=True)
        if d.get("type") == "machine"
    )


@app.get("/techniques")
async def techniques():
    """Sorted list of all technique node names in the knowledge graph."""
    retriever: HybridRetriever = _state["retriever"]
    graph = retriever.graph
    return sorted(
        n for n, d in graph.nodes(data=True)
        if d.get("type") == "technique"
    )


@app.get("/machine/{machine_name}")
async def machine_detail(machine_name: str):
    """Return metadata, techniques, tools, and CVEs for a single machine."""
    retriever: HybridRetriever = _state["retriever"]
    graph = retriever.graph

    if machine_name not in graph:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_name}' not found")

    # Resolve OS from outgoing "os" edge
    os_val = "unknown"
    for succ in graph.successors(machine_name):
        if graph.edges[machine_name, succ].get("rel") == "os":
            os_val = succ
            break

    # Techniques (successors with type=technique)
    techs = sorted(
        n for n in graph.successors(machine_name)
        if graph.nodes[n].get("type") == "technique"
    )

    return {
        "machine":    machine_name,
        "os":         os_val,
        "techniques": techs,
        "tools":      get_tools_for_machine(graph, machine_name),
        "cves":       get_cves_for_machine(graph, machine_name),
    }


@app.post("/retrieve")
async def retrieve_raw(req: RetrieveRequest):
    """Raw retrieval result (no synthesis) — useful for debug / eval."""
    retriever: HybridRetriever = _state["retriever"]

    result = retriever.retrieve(
        query=req.question,
        top_k=req.top_k,
    )

    return result
