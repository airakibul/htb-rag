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
from src.config import GEMINI_API_KEY, GROQ_API_KEY, RAW_DIR
from src.graph_builder import build_graph, save_graph


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
    """Exit early if API keys are missing or still set to placeholders."""
    missing: list[str] = []
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_key_here":
        missing.append("GEMINI_API_KEY")
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_key_here":
        missing.append("GROQ_API_KEY")

    if missing:
        print(f"❌ Missing API key(s): {', '.join(missing)}")
        print("   → Set them in .env and try again.")
        sys.exit(1)


def _validate_gemini() -> None:
    """Quick smoke-test of the Gemini Embedding API."""
    try:
        embedder.embed_texts(["test"])
        print("✅ Gemini API validated")
    except Exception as exc:
        print(f"❌ Gemini API error: {exc}")
        print("   → Check GEMINI_API_KEY in .env")
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
            print("Aborted.")
            sys.exit(0)


# ═════════════════════════════════════════════════════════════════════════════
#  File discovery
# ═════════════════════════════════════════════════════════════════════════════

def _get_files(single: str | None) -> list[Path]:
    """Return the list of ``.md`` files to ingest."""
    raw = Path(RAW_DIR)
    if not raw.exists():
        print(f"❌ RAW_DIR not found: {raw}")
        sys.exit(1)

    if single:
        target = raw / single
        if not target.exists():
            print(f"❌ File not found: {target}")
            sys.exit(1)
        return [target]

    files = sorted(raw.glob("*.md"))
    if not files:
        print(f"❌ No .md files found in {raw}")
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
                print(f"🚀 Overall progress: {curr}/{total} chunks ingested", flush=True)
                break
            except Exception as exc:
                err_str = str(exc).lower()
                if "429" in str(exc) or "rate" in err_str or "resource" in err_str:
                    print("⏳ Rate limited — waiting 60 s before retry…", flush=True)
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

    # ── 2. Validate Gemini API (skip for dry-run) ────────────────────────
    if not args.dry_run:
        _validate_gemini()

    # ── 3. Check existing collection ─────────────────────────────────────
    if not args.dry_run:
        _check_collection(is_single_file=bool(args.file))

    # ── 4. Disable image descriptions if requested ───────────────────────
    if args.skip_images:
        embedder.describe_image = lambda url: None      # noqa: ARG005
        print("⏭️  Image descriptions disabled (--skip-images)")

    # ── 5. Discover files ────────────────────────────────────────────────
    files = _get_files(args.file)
    print(f"\n📂 Found {len(files)} file(s) in {RAW_DIR}\n")

    # ── 6. Chunk every file ──────────────────────────────────────────────
    all_chunks: list[dict] = []
    processed = 0
    skipped   = 0

    for idx, md_path in enumerate(files, 1):
        try:
            print(f"📄 [{idx}/{len(files)}] Ingesting {md_path.name}...")
            chunks = chunk_file(str(md_path))
            all_chunks.extend(chunks)
            processed += 1
        except (IOError, OSError):
            print(f"⚠️  Skipped {md_path.name} (access denied)")
            skipped += 1

    print(f"\n🔢 Chunked {len(all_chunks)} chunks from {processed} files\n")

    # ── 7. Dry run → print stats and exit ────────────────────────────────
    if args.dry_run:
        elapsed = time.time() - t0
        mins, secs = divmod(int(elapsed), 60)
        print("─── Dry-run summary ───────────────────────────")
        print(f"  ✅ Files processed : {processed}")
        print(f"  ⚠️  Files skipped  : {skipped}")
        print(f"  📦 Total chunks   : {len(all_chunks)}")
        print(f"  ⏱  Time taken     : {mins}m {secs:02d}s")
        if all_chunks:
            print("\n─── Sample Chunks (Up to 3) ───────────────────")
            for i, chunk in enumerate(all_chunks[:3], 1):
                meta = chunk.get("metadata", {})
                snippet = chunk.get("text", "")[:120].replace("\n", " ")
                print(f"\n[Sample {i}]")
                print(f"  Metadata: {meta}")
                print(f"  Text Snippet: {snippet}...")
        return

    # ── 8. Store chunks in ChromaDB ──────────────────────────────────────
    _store_with_retry(all_chunks)

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

    print("\n═══ Ingestion complete ════════════════════════")
    print(f"  ✅ Files processed : {processed}")
    print(f"  ⚠️  Files skipped  : {skipped}")
    print(f"  📦 Total chunks   : {len(all_chunks)}")
    print(f"  🔗 Graph nodes    : {graph.number_of_nodes()}")
    print(f"  ⏱  Time taken     : {mins}m {secs:02d}s")


if __name__ == "__main__":
    main()
