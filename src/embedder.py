"""
embedder.py – Embedding & vision via Google Gemini, stored in ChromaDB.

Uses ``text-embedding-004`` for text embeddings and ``gemini-1.5-flash``
for image descriptions.  ChromaDB is the persistent vector store.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import time
from pathlib import Path
from typing import Any

import chromadb
import google.generativeai as genai
import numpy as np
import requests
from PIL import Image

from src.config import (
    CHROMA_DIR,
    EMBED_BATCH_SIZE,
    GEMINI_API_KEY,
    GEMINI_EMBED_MODEL,
    GEMINI_VISION_MODEL,
    IMAGE_CACHE,
)

# ── Configure Gemini ─────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)

# ── Regex / patterns ─────────────────────────────────────────────────────────
_IMG_URL_RE = re.compile(r"!\[.*?\]\((https?://\S+?)\)")
_DECORATIVE_PATTERNS = ("cover", "-diff.", "-radar.", "/icons/", "box-")


class FallbackVectorCollection:
    """Fallback vector storage backed by JSON and NumPy when ChromaDB fails."""

    def __init__(self, chroma_dir: str, collection_name: str = "htb_wiki") -> None:
        self.dir = Path(chroma_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.dir / f"{collection_name}_store.json"
        self._data: dict[str, dict[str, Any]] = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        if self.file_path.exists():
            try:
                return json.loads(self.file_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.file_path.write_text(json.dumps(self._data), encoding="utf-8")

    def count(self) -> int:
        return len(self._data)

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        for chunk_id, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            self._data[chunk_id] = {
                "id": chunk_id,
                "embedding": emb,
                "document": doc,
                "metadata": meta,
            }
        self._save()

    def get(self, include: list[str] | None = None, limit: int | None = None) -> dict[str, list[Any]]:
        items = list(self._data.values())
        if limit:
            items = items[:limit]
        docs = [item["document"] for item in items]
        metas = [item["metadata"] for item in items]
        return {"documents": docs, "metadatas": metas}

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, list[list[Any]]]:
        if not self._data or not query_embeddings:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        q_arr = np.array(query_embeddings[0], dtype=np.float32)

        candidates = []
        for item in self._data.values():
            meta = item["metadata"]
            if where and not self._matches_where(meta, where):
                continue
            v_arr = np.array(item["embedding"], dtype=np.float32)
            target_dim = min(len(q_arr), len(v_arr))
            q_sub = q_arr[:target_dim]
            v_sub = v_arr[:target_dim]
            norm_q = np.linalg.norm(q_sub)
            norm_v = np.linalg.norm(v_sub)
            if norm_q == 0 or norm_v == 0:
                dist = 1.0
            else:
                sim = float(np.dot(q_sub, v_sub) / (norm_q * norm_v))
                dist = max(0.0, 1.0 - sim)
            candidates.append((dist, item["document"], item["metadata"]))

        candidates.sort(key=lambda x: x[0])
        top = candidates[:n_results]

        dists = [c[0] for c in top]
        docs = [c[1] for c in top]
        metas = [c[2] for c in top]

        return {"documents": [docs], "metadatas": [metas], "distances": [dists]}

    def _matches_where(self, metadata: dict[str, Any], where: dict[str, Any]) -> bool:
        if not where:
            return True
        if "$and" in where:
            return all(self._matches_where(metadata, clause) for clause in where["$and"])
        for k, v in where.items():
            if metadata.get(k) != v:
                return False
        return True


# ═════════════════════════════════════════════════════════════════════════════
#  Text Embedding
# ═════════════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════════════
#  Text Embedding
# ═════════════════════════════════════════════════════════════════════════════

def _local_hash_embedding(text: str, dim: int = 768) -> list[float]:
    """Deterministic 768-dim feature hash vectorizer fallback."""
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return [0.0] * dim
    vec = np.zeros(dim, dtype=np.float32)
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % dim
        val = 1.0 if (h & 1) else -1.0
        vec[idx] += val
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed multiple texts using Gemini with fast local hash vectorizer fallback."""
    try:
        result = genai.embed_content(
            model=GEMINI_EMBED_MODEL,
            content=texts,
            task_type="RETRIEVAL_DOCUMENT",
        )
        return result["embedding"]
    except Exception as exc:
        err_str = str(exc).lower()
        if "429" in str(exc) or "rate" in err_str or "quota" in err_str:
            return [_local_hash_embedding(t) for t in texts]
        raise


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    try:
        result = genai.embed_content(
            model=GEMINI_EMBED_MODEL,
            content=text,
            task_type="RETRIEVAL_QUERY",
        )
        return result["embedding"]
    except Exception as exc:
        err_str = str(exc).lower()
        if "429" in str(exc) or "rate" in err_str or "quota" in err_str:
            return _local_hash_embedding(text)
        raise


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
    """Describe a screenshot using Gemini Vision (``gemini-1.5-flash``).

    Results are cached to :pydata:`IMAGE_CACHE`.
    Returns ``None`` on any error — never crashes.
    """
    try:
        cache = _load_image_cache()
        key = hashlib.md5(url.encode()).hexdigest()

        if key in cache:
            return cache[key]

        # Download image
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))

        # Vision model
        model = genai.GenerativeModel(GEMINI_VISION_MODEL)
        response = model.generate_content([_VISION_PROMPT, img])
        description = response.text.strip()

        # Update cache
        cache[key] = description
        _save_image_cache(cache)

        return description

    except Exception as exc:                       # noqa: BLE001
        print(f"⚠️  describe_image failed for {url}: {exc}")
        return None


def is_decorative_image(url: str) -> bool:
    """Return ``True`` if *url* matches a known decorative-image pattern."""
    low = url.lower()
    return any(pat in low for pat in _DECORATIVE_PATTERNS)


def get_image_urls(markdown_text: str) -> list[str]:
    """Extract HTTP(S) image URLs from markdown ``![…](url)`` syntax."""
    return _IMG_URL_RE.findall(markdown_text)


# ═════════════════════════════════════════════════════════════════════════════
#  ChromaDB Storage
# ═════════════════════════════════════════════════════════════════════════════

def _get_client() -> chromadb.ClientAPI:
    """Return a ChromaDB ``PersistentClient`` rooted at ``CHROMA_DIR``."""
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(
    collection_name: str = "htb_wiki",
) -> Any:
    """Return the ChromaDB collection or FallbackVectorCollection on failure."""
    try:
        client = _get_client()
        return client.get_or_create_collection(name=collection_name)
    except Exception as exc:
        return FallbackVectorCollection(CHROMA_DIR, collection_name)


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
    total = len(all_chunks)

    # ── Batch embed & upsert ─────────────────────────────────────────────
    for start in range(0, total, EMBED_BATCH_SIZE):
        batch = all_chunks[start : start + EMBED_BATCH_SIZE]
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
            print(f"📦 Stored {stored}/{total} chunks...")


# ═════════════════════════════════════════════════════════════════════════════
#  Retrieval helpers
# ═════════════════════════════════════════════════════════════════════════════

def get_all_documents() -> list[dict[str, Any]]:
    """Return every document from the ChromaDB collection.

    Each item is ``{"text": …, "metadata": …}``.
    Used by the retriever to build its BM25 index.
    """
    collection = get_collection()
    results = collection.get(include=["documents", "metadatas"])

    docs: list[dict[str, Any]] = []
    for text, meta in zip(results["documents"], results["metadatas"]):
        docs.append({"text": text, "metadata": meta})

    return docs
