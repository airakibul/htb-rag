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
    except Exception:  # noqa: BLE001, S110
        pass

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)


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


def get_retriever() -> HybridRetriever:
    """Safe getter for the HybridRetriever singleton."""
    if "retriever" not in _state:
        _state["retriever"] = HybridRetriever()
    return _state["retriever"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the HybridRetriever singleton on startup."""
    retriever = get_retriever()

    if not retriever.docs:
        logger.warning("⚠️  No chunks indexed. Run: python -m src.ingest")

    # Pre-warm cross-encoder (lazy load on first use is also fine)
    try:
        from src.reranker import _get_model
        _get_model()
    except Exception:  # noqa: BLE001, S110
        pass  # Non-critical — will lazy-load on first query

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
async def _global_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# ── Static Files & Dashboard Mount ──────────────────────────────────────────
_static_dir = project_root / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def index():
    """Serve the interactive web dashboard."""
    index_file = _static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "ok", "message": "HTB RAG API is running. Visit /docs for Swagger UI."})


# ═════════════════════════════════════════════════════════════════════════════
#  Endpoints
# ═════════════════════════════════════════════════════════════════════════════


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Retrieve context **and** synthesise a cited answer."""
    retriever: HybridRetriever = get_retriever()

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
    retriever: HybridRetriever = get_retriever()
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
    retriever: HybridRetriever = get_retriever()
    graph = retriever.graph
    return sorted(
        n for n, d in graph.nodes(data=True)
        if d.get("type") == "machine"
    )


@app.get("/techniques")
async def techniques():
    """Sorted list of all technique node names in the knowledge graph."""
    retriever: HybridRetriever = get_retriever()
    graph = retriever.graph
    return sorted(
        n for n, d in graph.nodes(data=True)
        if d.get("type") == "technique"
    )


@app.get("/machine/{machine_name}")
async def machine_detail(machine_name: str):
    """Return metadata, techniques, tools, and CVEs for a single machine."""
    retriever: HybridRetriever = get_retriever()
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
    retriever: HybridRetriever = get_retriever()

    result = retriever.retrieve(
        query=req.question,
        top_k=req.top_k,
    )

    return result
