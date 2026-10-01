"""
chroma_store.py – VectorStore implementation using ChromaDB.

Concrete adapter implementing the domain VectorStore interface with
automatic fallback to JSON/NumPy vector storage if ChromaDB fails.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import chromadb
import numpy as np

from src.config import CHROMA_DIR
from src.domain.interfaces import VectorStore

logger = logging.getLogger(__name__)


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
            except (json.JSONDecodeError, OSError):
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

    def get(
        self, include: list[str] | None = None, limit: int | None = None
    ) -> dict[str, list[Any]]:
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


class ChromaStore(VectorStore):
    """VectorStore implementation using ChromaDB with FallbackVectorCollection support."""

    def __init__(
        self, chroma_dir: str = CHROMA_DIR, collection_name: str = "htb_wiki"
    ) -> None:
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> Any:
        Path(self.chroma_dir).mkdir(parents=True, exist_ok=True)
        try:
            client = chromadb.PersistentClient(path=self.chroma_dir)
            return client.get_or_create_collection(name=self.collection_name)
        except Exception as exc:
            logger.warning(
                f"ChromaDB client error ({exc}), using FallbackVectorCollection"
            )
            return FallbackVectorCollection(self.chroma_dir, self.collection_name)

    def query(
        self,
        embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return the top_k nearest-neighbour hits from ChromaDB."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        raw = self.collection.query(**kwargs)
        results: list[dict[str, Any]] = []
        if not raw or not raw.get("documents") or not raw["documents"][0]:
            return results

        docs = raw["documents"][0]
        metas = raw["metadatas"][0]
        dists = raw["distances"][0]

        for rank, (text, meta, dist) in enumerate(zip(docs, metas, dists), 1):
            results.append({
                "text": text,
                "metadata": meta,
                "score": float(dist),
                "rank": rank,
            })
        return results

    def get_all_documents(self) -> list[dict[str, Any]]:
        """Return every document from the ChromaDB collection."""
        results = self.collection.get(include=["documents", "metadatas"])
        docs: list[dict[str, Any]] = []
        for text, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            docs.append({"text": text, "metadata": meta})
        return docs

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert documents with their embeddings and metadata into ChromaDB."""
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
