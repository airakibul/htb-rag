"""
ingest_missing.py – Incrementally ingest writeups that are not yet in ChromaDB.

1. Inspects existing sources in ChromaDB.
2. Identifies all .md files in RAW_DIR that are missing.
3. Chunks them using the updated chunker (skipping distractor sections).
4. Stores chunks in ChromaDB with rate-limit handling.
5. Rebuilds and saves the NetworkX knowledge graph.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src import embedder
from src.chunker import chunk_file
from src.config import RAW_DIR
from src.graph_builder import build_graph, save_graph


def main():
    parser = argparse.ArgumentParser(description="Ingest missing HTB writeup files into ChromaDB")
    parser.add_argument("--skip-images", action="store_true", default=True,
                        help="Skip Gemini Vision calls on images (default: True for speed)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of missing files to process")
    args = parser.parse_args()

    if args.skip_images:
        embedder.describe_image = lambda url: None
        print("⏭️  Image descriptions skipped for faster ingestion.")

    t0 = time.time()

    # 1. Inspect existing sources
    print("🔍 Checking existing documents in ChromaDB...")
    docs = embedder.get_all_documents()
    existing_sources = {d["metadata"]["source"] for d in docs if d.get("metadata", {}).get("source")}
    print(f"📦 Currently in DB: {len(existing_sources)} machines ({len(docs)} chunks)")

    # 2. Identify missing files
    all_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.md")))
    missing_files = [
        f for f in all_files
        if os.path.splitext(os.path.basename(f))[0] not in existing_sources
    ]

    print(f"📂 Total raw files: {len(all_files)}")
    print(f"🚨 Missing files to ingest: {len(missing_files)}")

    if not missing_files:
        print("✅ No missing files. Database is up to date!")
        return

    if args.limit:
        missing_files = missing_files[:args.limit]
        print(f"⚙️ Limiting to first {len(missing_files)} missing files.")

    # 3. Chunk missing files
    print("\n📄 Chunking missing files...")
    new_chunks = []
    chunked_files = 0
    for idx, fpath in enumerate(missing_files, 1):
        fname = os.path.basename(fpath)
        try:
            chunks = chunk_file(fpath)
            new_chunks.extend(chunks)
            chunked_files += 1
            if idx % 25 == 0 or idx == len(missing_files):
                print(f"  [{idx}/{len(missing_files)}] Chunked {fname} (total new chunks: {len(new_chunks)})")
        except Exception as e:
            print(f"  ⚠️ Error chunking {fname}: {e}")

    print(f"\n🔢 Generated {len(new_chunks)} chunks from {chunked_files} files.")

    # 4. Store in ChromaDB
    print("\n💾 Embedding and storing chunks in ChromaDB...")
    total = len(new_chunks)
    group_size = 450
    for start in range(0, total, group_size):
        group = new_chunks[start : start + group_size]
        while True:
            try:
                embedder.store_chunks(group)
                curr = min(start + group_size, total)
                print(f"  🚀 Progress: {curr}/{total} chunks stored", flush=True)
                break
            except Exception as exc:
                err_str = str(exc).lower()
                if "429" in str(exc) or "rate" in err_str or "quota" in err_str or "resource" in err_str:
                    print("  ⏳ Rate limited — waiting 60s before retry...", flush=True)
                    time.sleep(60)
                else:
                    raise

    # 5. Rebuild and save NetworkX graph
    print("\n🕸️  Rebuilding NetworkX knowledge graph with ALL chunks...")
    all_stored = embedder.get_all_documents()
    full_chunks = []
    for doc in all_stored:
        c = dict(doc.get("metadata", {}))
        c["text"] = doc.get("text", "")
        full_chunks.append(c)

    graph = build_graph(full_chunks)
    save_graph(graph)

    elapsed = time.time() - t0
    mins, secs = divmod(int(elapsed), 60)
    print("\n═══ Incremental Ingestion Complete ════════════")
    print(f"  ✅ New files ingested : {chunked_files}")
    print(f"  📦 Total chunks in DB : {len(all_stored)}")
    print(f"  🔗 Total graph nodes  : {graph.number_of_nodes()}")
    print(f"  ⏱  Time elapsed       : {mins}m {secs:02d}s\n")


if __name__ == "__main__":
    main()
