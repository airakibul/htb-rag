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
RAW_DIR = os.getenv("RAW_DIR", r"c:\Brain Station 23\htb-wiki\raw")
CHROMA_DIR = "./db/chroma"
GRAPH_PATH = "./graph/htb_graph.pkl"
IMAGE_CACHE = "./cache/image_cache.json"

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Model identifiers ────────────────────────────────────────────────────────
GEMINI_EMBED_MODEL = "models/gemini-embedding-001"
GEMINI_VISION_MODEL = "models/gemini-2.5-flash"
GROQ_LLM_MODEL = "openai/gpt-oss-120b"

# ── Tuning knobs ──────────────────────────────────────────────────────────────
EMBED_BATCH_SIZE = 90
CHUNK_TOKEN_LIMIT = 600        # ≈ 2 400 characters
TOP_K = 8
