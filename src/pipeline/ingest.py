"""
ingest.py – Orchestrates the full HTB RAG ingestion pipeline.

Follows Clean Architecture and SOLID principles:
- Uses VectorStore, EmbeddingService, and ChunkingStrategy domain interfaces.
- IngestionPipeline encapsulates end-to-end chunking, embedding, vector storage,
  and knowledge graph generation.

Usage::

    python -m src.pipeline.ingest                     # full ingest
    python -m src.pipeline.ingest --file htb-box.md   # single file
    python -m src.pipeline.ingest --dry-run           # chunk + stats, no storage
    python -m src.pipeline.ingest --skip-images       # skip Gemini Vision calls
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Fix sys.path for direct script execution
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Reconfigure stdout for unicode on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from src.config import (
    EMBED_BATCH_SIZE,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    RAW_DIR,
)
from src.domain.interfaces import (
    ChunkingStrategy,
    EmbeddingService,
    VectorStore,
)
from src.graph.builder import build_graph, save_graph
from src.pipeline.chunker import MarkdownChunker, chunk_file

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  CLI Argument Parser
# ═════════════════════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="HTB RAG ingestion pipeline")
    p.add_argument("--file",        type=str, default=None,
                   help="Ingest a single .md file from RAW_DIR")
    p.add_argument("--dry-run",     action="store_true",
                   help="Chunk + print stats — no embedding / storage")
    p.add_argument("--skip-images", action="store_true",
                   help="Skip image description (faster ingest)")
    return p.parse_args()


# ═════════════════════════════════════════════════════════════════════════════
#  Pre-flight checks
# ═════════════════════════════════════════════════════════════════════════════

def _validate_keys() -> None:
    """Check LLM and service API keys."""
    configured: list[str] = []
    if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_key_here":
        configured.append("OpenRouter")
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_key_here":
        configured.append("Gemini")

    if configured:
        logger.info(f"🔑 Active LLM provider(s): {', '.join(configured)}")
    else:
        logger.warning("⚠️ No LLM API key configured (OPENROUTER_API_KEY, GROQ_API_KEY, or GEMINI_API_KEY).")
        logger.warning("   Synthesis will run in fallback/offline mode until a key is added in .env.")


def _validate_embedder(embedding_service: EmbeddingService | None = None) -> None:
    """Quick smoke-test of the EmbeddingService."""
    try:
        if embedding_service is None:
            from src.container import create_embedding_service
            embedding_service = create_embedding_service()
        vecs = embedding_service.embed_texts(["test smoke"])
        dim = len(vecs[0]) if vecs else 0
        logger.info(f"✅ SentenceTransformer embedding engine ready (dim={dim})")
    except Exception as exc:
        logger.error(f"❌ Embedder error: {exc}")
        sys.exit(1)


def _check_collection(vector_store: VectorStore | None = None, is_single_file: bool = False) -> None:
    """Prompt the user if the vector store already contains documents."""
    if is_single_file:
        return
    if vector_store is None:
        from src.container import create_vector_store
        vector_store = create_vector_store()
    existing_docs = vector_store.get_all_documents()
    count = len(existing_docs)
    if count > 0:
        if not sys.stdin.isatty():
            return
        resp = input(f"VectorStore has {count} chunks. Re-ingest? [y/N] ")
        if resp.strip().lower() != "y":
            logger.info("Aborted.")
            sys.exit(0)


# ═════════════════════════════════════════════════════════════════════════════
#  File discovery
# ═════════════════════════════════════════════════════════════════════════════

def _get_files(single: str | None) -> list[Path]:
    """Return the list of ``.md`` files to ingest."""
    raw = Path(RAW_DIR)
    if not raw.exists():
        logger.error(f"❌ RAW_DIR not found: {raw}")
        sys.exit(1)

    if single:
        target = raw / single
        if not target.exists():
            logger.error(f"❌ File not found: {target}")
            sys.exit(1)
        return [target]

    files = sorted(raw.glob("*.md"))
    if not files:
        logger.error(f"❌ No .md files found in {raw}")
        sys.exit(1)
    return files


# ═════════════════════════════════════════════════════════════════════════════
#  IngestionPipeline Class (Clean Architecture & SRP)
# ═════════════════════════════════════════════════════════════════════════════

class IngestionPipeline:
    """Coordinates document chunking, embedding, vector storage, and graph creation."""

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_service: EmbeddingService | None = None,
        chunking_strategy: ChunkingStrategy | None = None,
    ) -> None:
        from src.container import (
            create_embedding_service,
            create_vector_store,
        )

        self.vector_store: VectorStore = vector_store or create_vector_store()
        self.embedding_service: EmbeddingService = (
            embedding_service or create_embedding_service()
        )
        self.chunking_strategy: ChunkingStrategy = (
            chunking_strategy or MarkdownChunker()
        )

    def store_chunks(
        self,
        chunks: list[dict[str, Any]],
        skip_images: bool = False,
        batch_size: int = EMBED_BATCH_SIZE,
    ) -> int:
        """Embed and upsert chunks into VectorStore, handling multimodal image descriptions."""
        from src.embedder import (
            _chunk_id,
            _serialize_metadata,
            describe_image,
            get_image_urls,
            is_decorative_image,
        )

        image_chunks: list[dict[str, Any]] = []
        if not skip_images:
            for chunk in chunks:
                for url in get_image_urls(chunk.get("text", "")):
                    if is_decorative_image(url):
                        continue
                    desc = describe_image(url)
                    if desc:
                        img_chunk = {k: chunk[k] for k in chunk if k != "text"}
                        img_chunk["text"] = f"[Image description] {desc}"
                        img_chunk["chunk_type"] = "image_desc"
                        image_chunks.append(img_chunk)

        all_chunks = chunks + image_chunks

        # Deduplicate chunks by ID
        deduped: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for c in all_chunks:
            cid = _chunk_id(c)
            if cid not in seen_ids:
                seen_ids.add(cid)
                deduped.append(c)

        total = len(deduped)
        for start in range(0, total, batch_size):
            batch = deduped[start : start + batch_size]
            texts = [c["text"] for c in batch]
            embeddings = self.embedding_service.embed_texts(texts)
            ids = [_chunk_id(c) for c in batch]
            metas = [_serialize_metadata(c) for c in batch]

            self.vector_store.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metas,
            )
            stored = min(start + batch_size, total)
            if stored % 100 < batch_size or stored == total:
                logger.info(f"📦 Stored {stored}/{total} chunks in VectorStore...")

        return total

    def build_and_save_graph(self) -> Any:
        """Construct and persist the Knowledge Graph from stored documents."""
        all_stored = self.vector_store.get_all_documents()
        full_chunks = []
        for doc in all_stored:
            c = dict(doc.get("metadata", {}))
            c["text"] = doc.get("text", "")
            full_chunks.append(c)
        graph = build_graph(full_chunks)
        save_graph(graph)
        return graph


def _store_with_retry(
    chunks: list[dict[str, Any]],
    group_size: int = 450,
    pipeline: IngestionPipeline | None = None,
    skip_images: bool = False,
) -> None:
    """Feed chunks to IngestionPipeline in groups with backoff retry."""
    pipe = pipeline or IngestionPipeline()
    total = len(chunks)
    for start in range(0, total, group_size):
        group = chunks[start : start + group_size]
        while True:
            try:
                pipe.store_chunks(group, skip_images=skip_images)
                curr = min(start + group_size, total)
                logger.info(f"🚀 Overall progress: {curr}/{total} chunks ingested")
                break
            except Exception as exc:
                err_str = str(exc).lower()
                if "429" in str(exc) or "rate" in err_str or "resource" in err_str:
                    logger.warning("⏳ Rate limited — waiting 60 s before retry…")
                    time.sleep(60)
                else:
                    raise


# ═════════════════════════════════════════════════════════════════════════════
#  Main entry-point
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    args = _parse_args()
    t0 = time.time()

    pipeline = IngestionPipeline()

    # 1. Validate API keys
    _validate_keys()

    # 2. Validate Embedder
    if not args.dry_run:
        _validate_embedder(pipeline.embedding_service)

    # 3. Check existing collection
    if not args.dry_run:
        _check_collection(pipeline.vector_store, is_single_file=bool(args.file))

    # 4. Discover files
    files = _get_files(args.file)
    logger.info(f"📂 Found {len(files)} file(s) in {RAW_DIR}")

    # 5. Chunk every file
    all_chunks: list[dict] = []
    processed = 0
    skipped   = 0

    from src.embedder import _chunk_id

    for idx, md_path in enumerate(files, 1):
        try:
            logger.info(f"📄 [{idx}/{len(files)}] Ingesting {md_path.name}...")
            chunks = pipeline.chunking_strategy.chunk_file(md_path)
            all_chunks.extend(chunks)
            processed += 1
        except (IOError, OSError):
            logger.warning(f"⚠️  Skipped {md_path.name} (access denied)")
            skipped += 1

    # 6. Deduplicate chunks by ID
    unique_chunks: list[dict] = []
    seen_ids: set[str] = set()
    for c in all_chunks:
        cid = _chunk_id(c)
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique_chunks.append(c)

    logger.info(f"🔢 Chunked {len(all_chunks)} chunks ({len(unique_chunks)} unique) from {processed} files")

    # 7. Dry run → print stats and exit
    if args.dry_run:
        elapsed = time.time() - t0
        mins, secs = divmod(int(elapsed), 60)
        logger.info("─── Dry-run summary ───────────────────────────")
        logger.info(f"  ✅ Files processed : {processed}")
        logger.info(f"  ⚠️  Files skipped  : {skipped}")
        logger.info(f"  📦 Total chunks   : {len(unique_chunks)}")
        logger.info(f"  ⏱  Time taken     : {mins}m {secs:02d}s")
        if unique_chunks:
            logger.info("─── Sample Chunks (Up to 3) ───────────────────")
            for i, chunk in enumerate(unique_chunks[:3], 1):
                meta = chunk.get("metadata", {})
                snippet = chunk.get("text", "")[:120].replace("\n", " ")
                logger.info(f"[Sample {i}] Metadata: {meta} | Snippet: {snippet}...")
        return

    # 8. Store chunks in VectorStore
    _store_with_retry(unique_chunks, pipeline=pipeline, skip_images=args.skip_images)

    # 9. Build & save knowledge graph
    graph = pipeline.build_and_save_graph()

    # 10. Final summary
    elapsed = time.time() - t0
    mins, secs = divmod(int(elapsed), 60)

    logger.info("═══ Ingestion complete ════════════════════════")
    logger.info(f"  ✅ Files processed : {processed}")
    logger.info(f"  ⚠️  Files skipped  : {skipped}")
    logger.info(f"  📦 Total chunks   : {len(all_chunks)}")
    n_mach = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "machine")
    n_tech = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "technique")
    n_cve  = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "cve")
    n_tool = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "tool")
    logger.info(f"  🔗 Graph nodes    : {graph.number_of_nodes()} (edges: {graph.number_of_edges()})")
    logger.info(f"     → Machines: {n_mach}, Techniques: {n_tech}, CVEs: {n_cve}, Tools: {n_tool}")
    logger.info(f"  ⏱  Time taken     : {mins}m {secs:02d}s")


if __name__ == "__main__":
    main()
