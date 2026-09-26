"""
ingest.py – Orchestrates the full HTB RAG ingestion pipeline.

Usage::

    python -m src.ingest                     # full ingest
    python -m src.ingest --file htb-box.md   # single file
    python -m src.ingest --dry-run           # chunk + stats, no storage
    python -m src.ingest --skip-images       # skip Gemini Vision calls
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Fix sys.path for direct script execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Reconfigure stdout for unicode on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from src import embedder
from src.chunker import chunk_file
from src.config import GEMINI_API_KEY, OPENROUTER_API_KEY, RAW_DIR
from src.graph_builder import build_graph, save_graph

logger = logging.getLogger(__name__)



# ═════════════════════════════════════════════════════════════════════════════
#  CLI
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


def _validate_embedder() -> None:
    """Quick smoke-test of the SentenceTransformer embedding model."""
    try:
        vecs = embedder.embed_texts(["test smoke"])
        dim = len(vecs[0]) if vecs else 0
        logger.info(f"✅ SentenceTransformer embedding engine ready (dim={dim})")
    except Exception as exc:
        logger.error(f"❌ Embedder error: {exc}")
        sys.exit(1)


def _check_collection(is_single_file: bool = False) -> None:
    """Prompt the user if the ChromaDB collection already contains data."""
    if is_single_file:
        return
    collection = embedder.get_collection()
    count = collection.count()
    if count > 0:
        if not sys.stdin.isatty():
            return
        resp = input(f"Collection has {count} chunks. Re-ingest? [y/N] ")
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
#  Storage with rate-limit retry
# ═════════════════════════════════════════════════════════════════════════════

def _store_with_retry(
    chunks: list[dict],
    group_size: int = 450,
) -> None:
    """Feed chunks to ``embedder.store_chunks`` in groups.

    If a Gemini 429 (rate-limit) error is detected the group is retried
    after a 60-second cool-down.
    """
    total = len(chunks)
    for start in range(0, total, group_size):
        group = chunks[start : start + group_size]
        while True:
            try:
                embedder.store_chunks(group)
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
#  Main
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    args = _parse_args()
    t0 = time.time()

    # ── 1. Validate API keys ─────────────────────────────────────────────
    _validate_keys()

    # ── 2. Validate Embedder (skip for dry-run) ─────────────────────────
    if not args.dry_run:
        _validate_embedder()

    # ── 3. Check existing collection ─────────────────────────────────────
    if not args.dry_run:
        _check_collection(is_single_file=bool(args.file))

    # ── 4. Disable image descriptions if requested ───────────────────────
    if args.skip_images:
        embedder.describe_image = lambda url: None      # noqa: ARG005
        logger.info("⏭️  Image descriptions disabled (--skip-images)")

    # ── 5. Discover files ────────────────────────────────────────────────
    files = _get_files(args.file)
    logger.info(f"📂 Found {len(files)} file(s) in {RAW_DIR}")

    # ── 6. Chunk every file ──────────────────────────────────────────────
    all_chunks: list[dict] = []
    processed = 0
    skipped   = 0

    for idx, md_path in enumerate(files, 1):
        try:
            logger.info(f"📄 [{idx}/{len(files)}] Ingesting {md_path.name}...")
            chunks = chunk_file(str(md_path))
            all_chunks.extend(chunks)
            processed += 1
        except (IOError, OSError):
            logger.warning(f"⚠️  Skipped {md_path.name} (access denied)")
            skipped += 1

    # ── 7. Deduplicate chunks by ID ──────────────────────────────────────
    unique_chunks: list[dict] = []
    seen_ids: set[str] = set()
    for c in all_chunks:
        cid = embedder._chunk_id(c)
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique_chunks.append(c)

    logger.info(f"🔢 Chunked {len(all_chunks)} chunks ({len(unique_chunks)} unique) from {processed} files")

    # ── 8. Dry run → print stats and exit ────────────────────────────────
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

    # ── 9. Store chunks in ChromaDB ──────────────────────────────────────
    _store_with_retry(unique_chunks)

    # ── 9. Build & save knowledge graph ──────────────────────────────────
    all_stored = embedder.get_all_documents()
    full_chunks = []
    for doc in all_stored:
        c = dict(doc.get("metadata", {}))
        c["text"] = doc.get("text", "")
        full_chunks.append(c)
    graph = build_graph(full_chunks)
    save_graph(graph)

    # ── 10. Final summary ────────────────────────────────────────────────
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
