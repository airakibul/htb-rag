"""Backward-compatible shim — delegates to src.api.server."""

from src.api.routes import router  # noqa: F401
from src.api.schemas import (  # noqa: F401
    QueryRequest,
    QueryResponse,
    RetrieveRequest,
)
from src.api.server import (  # noqa: F401
    app,
    get_retriever,
    lifespan,
)

__all__ = [
    "QueryRequest",
    "QueryResponse",
    "RetrieveRequest",
    "app",
    "get_retriever",
    "lifespan",
    "router",
]
