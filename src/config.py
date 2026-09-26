"""
config.py – Centralised configuration for the HTB RAG pipeline.

Loads secrets from .env and exposes paths / model names as module-level
constants so every other module can simply `from src.config import …`.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW_DIR = os.getenv("RAW_DIR", "./raw")
CHROMA_DIR = "./db/chroma"
GRAPH_PATH = "./graph/htb_graph.json"

IMAGE_CACHE = "./cache/image_cache.json"

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Model identifiers ────────────────────────────────────────────────────────
# Groq LLM Configuration (Ultra-fast LPU inference)
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# OpenRouter LLM Configuration (Fallback)
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
OPENROUTER_FALLBACK_MODELS = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/free",
]

# Local Sentence Transformers Embedding
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
GEMINI_VISION_MODEL = "models/gemini-2.5-flash"


# ── Tuning knobs ──────────────────────────────────────────────────────────────
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "128"))
CHUNK_TOKEN_LIMIT = 600        # ≈ 2 400 characters
TOP_K = 8

# ── Structured Logging ────────────────────────────────────────────────────────
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

