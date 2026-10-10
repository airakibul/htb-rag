"""
embedder.py – Embedding & vision via Google Gemini, stored in ChromaDB.

Backward-compatible shim delegating to infrastructure adapters (SentenceTransformerEmbeddingService,
ChromaStore) while maintaining vision and chunk formatting helpers.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import re
from pathlib import Path
from typing import Any

import chromadb
import requests
from PIL import Image

from src.config import (
    CHROMA_DIR,
    EMBED_BATCH_SIZE,
    EMBEDDING_MODEL_NAME,
    GEMINI_API_KEY,
    GEMINI_VISION_MODEL,
    IMAGE_CACHE,
)
from src.infrastructure.chroma_store import (
    ChromaStore,
    FallbackVectorCollection,
)
from src.infrastructure.sentence_transformer import (
    SentenceTransformerEmbeddingService,
    _get_embed_model,
    _local_hash_embedding,
    embed_query,
    embed_texts,
)

logger = logging.getLogger(__name__)

# ── Gemini vision client is configured on-demand in describe_image ─────────

# ── Regex / patterns ─────────────────────────────────────────────────────────
_IMG_URL_RE = re.compile(r"!\[.*?\]\((https?://\S+?)\)")
_DECORATIVE_PATTERNS = ("cover", "-diff.", "-radar.", "/icons/", "box-")

_default_store = ChromaStore()


def _get_client() -> Any:
    """Return a ChromaDB ``PersistentClient`` rooted at ``CHROMA_DIR``."""
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(
    collection_name: str = "htb_wiki",
) -> Any:
    """Return the ChromaDB collection or FallbackVectorCollection on failure."""
    return _default_store.collection


def _serialize_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    """Convert chunk metadata for ChromaDB storage.

    List fields are joined into comma-separated strings because
    ChromaDB metadata values must be scalars.
    """
    meta: dict[str, Any] = {}
    for key in (
        "source", "machine_name", "os", "difficulty",
        "h2", "h3", "breadcrumb", "chunk_type",
        "has_cve", "has_code", "attack_phase", "stub_file",
    ):
        if key in chunk:
            meta[key] = chunk[key]

    # Lists → comma-separated strings
    meta["cve_ids"] = ", ".join(chunk.get("cve_ids", [])) or ""
    meta["tools_mentioned"] = ", ".join(chunk.get("tools_mentioned", [])) or ""

    return meta


def _chunk_id(chunk: dict[str, Any]) -> str:
    """Generate a deterministic, collision-free ID for a chunk.

    Uses full text MD5 hash rather than Python's hash() so IDs are stable across
    process restarts and never overwrite distinct sub-chunks within the same section.
    """
    source = chunk.get("source", "")
    h2     = chunk.get("h2", "")
    h3     = chunk.get("h3", "")
    h4     = chunk.get("h4", "")
    text   = chunk.get("text", "")
    sig    = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
    return f"{source}__{h2}__{h3}__{h4}__{sig}"


# ═════════════════════════════════════════════════════════════════════════════
#  Image Vision
# ═════════════════════════════════════════════════════════════════════════════

_VISION_PROMPT = (
    "You are a cybersecurity analyst. Describe this screenshot. "
    "Focus on: tool name, command used, output shown, "
    "usernames, IP addresses, permissions, key security findings. "
    "Be concise and technical."
)


def _load_image_cache() -> dict[str, str]:
    """Load the image-description cache from disk (create if missing)."""
    path = Path(IMAGE_CACHE)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_image_cache(cache: dict[str, str]) -> None:
    """Persist the image-description cache to disk."""
    path = Path(IMAGE_CACHE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def describe_image(url: str) -> str | None:
    """Describe a screenshot using Gemini Vision (``gemini-2.5-flash``).

    Results are cached to :pydata:`IMAGE_CACHE`.
    Returns ``None`` on any error or missing key — never crashes.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_key_here":
        return None
    try:
        cache = _load_image_cache()
        key = hashlib.md5(url.encode()).hexdigest()

        if key in cache:
            return cache[key]

        # Download image
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))

        # Vision model via google.genai or fallback
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_VISION_MODEL,
                contents=[_VISION_PROMPT, img],
            )
            description = (response.text or "").strip()
        except ImportError:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=GEMINI_API_KEY)
            model = legacy_genai.GenerativeModel(GEMINI_VISION_MODEL)
            response = model.generate_content([_VISION_PROMPT, img])
            description = (response.text or "").strip()

        # Update cache
        cache[key] = description
        _save_image_cache(cache)

        return description

    except Exception as exc:                       # noqa: BLE001
        logger.warning(f"⚠️  describe_image failed for {url}: {exc}")
        return None


def is_decorative_image(url: str) -> bool:
    """Return ``True`` if *url* matches a known decorative-image pattern."""
    low = url.lower()
    return any(pat in low for pat in _DECORATIVE_PATTERNS)


def get_image_urls(markdown_text: str) -> list[str]:
    """Extract HTTP(S) image URLs from markdown ``![…](url)`` syntax."""
    return _IMG_URL_RE.findall(markdown_text)


def store_chunks(
    chunks: list[dict[str, Any]],
    collection_name: str = "htb_wiki",
) -> None:
    """Embed and store all chunks in ChromaDB.

    Also processes non-decorative images found in chunk text: describes
    them via Gemini Vision and stores the descriptions as additional
    ``image_desc`` chunks.
    """
    collection = get_collection(collection_name)

    # ── Collect image-description chunks ─────────────────────────────────
    image_chunks: list[dict[str, Any]] = []

    for chunk in chunks:
        for url in get_image_urls(chunk.get("text", "")):
            if is_decorative_image(url):
                continue
            desc = describe_image(url)
            if desc:
                img_chunk = {
                    k: chunk[k] for k in chunk if k != "text"
                }
                img_chunk["text"] = f"[Image description] {desc}"
                img_chunk["chunk_type"] = "image_desc"
                image_chunks.append(img_chunk)

    all_chunks = chunks + image_chunks

    # ── Deduplicate chunks by ID to prevent DuplicateIDError in ChromaDB ─
    deduped_chunks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for c in all_chunks:
        cid = _chunk_id(c)
        if cid not in seen_ids:
            seen_ids.add(cid)
            deduped_chunks.append(c)

    total = len(deduped_chunks)

    # ── Batch embed & upsert ─────────────────────────────────────────────
    for start in range(0, total, EMBED_BATCH_SIZE):
        batch = deduped_chunks[start : start + EMBED_BATCH_SIZE]
        texts = [c["text"] for c in batch]

        embeddings = embed_texts(texts)

        ids   = [_chunk_id(c)           for c in batch]
        metas = [_serialize_metadata(c) for c in batch]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metas,
        )

        stored = min(start + EMBED_BATCH_SIZE, total)
        if stored % 100 < EMBED_BATCH_SIZE or stored == total:
            logger.info(f"📦 Stored {stored}/{total} chunks...")


def get_all_documents() -> list[dict[str, Any]]:
    """Return every document from the ChromaDB collection."""
    return _default_store.get_all_documents()


__all__ = [
    "FallbackVectorCollection",
    "_chunk_id",
    "_get_client",
    "_get_embed_model",
    "_load_image_cache",
    "_local_hash_embedding",
    "_save_image_cache",
    "_serialize_metadata",
    "describe_image",
    "embed_query",
    "embed_texts",
    "get_all_documents",
    "get_collection",
    "get_image_urls",
    "is_decorative_image",
    "store_chunks",
]
