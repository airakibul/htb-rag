"""
server.py – FastAPI server initialization, lifespan, CORS, static mount, and app instance.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Add project root to sys.path if missing
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001, S110
        pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.pipeline.retriever import HybridRetriever

logger = logging.getLogger(__name__)

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
        from src.infrastructure.cross_encoder import _get_model
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

# ── Include API Routes ──────────────────────────────────────────────────────
app.include_router(router)
