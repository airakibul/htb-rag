"""
evaluator.py – Automated RAG evaluation harness.

Parses ``answer_key.md``, queries the running API, computes
Recall / Precision per question, and writes results + generated
answers to disk.

Usage::

    python eval/evaluator.py                     # all 15 questions
    python eval/evaluator.py --questions 1,6,7   # subset
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests

# ── Paths ────────────────────────────────────────────────────────────────────
EVAL_DIR      = Path(__file__).resolve().parent
PROJECT_ROOT  = EVAL_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ANSWER_KEY    = EVAL_DIR / "answer_key.md"
TEST_QS       = EVAL_DIR / "test_questions.md"
RESULTS_OUT   = EVAL_DIR / "results.md"
ANSWERS_OUT   = EVAL_DIR / "answers_generated.md"
API_BASE      = "http://127.0.0.1:8000"


# ═════════════════════════════════════════════════════════════════════════════
#  Answer-key parser
# ═════════════════════════════════════════════════════════════════════════════

def _parse_answer_key(filepath: Path = ANSWER_KEY) -> dict[int, dict[str, Any]]:
    """Parse ``answer_key.md`` into ``{q_number: {title, machines}}``."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")

    entries: dict[int, dict[str, Any]] = {}
    # Match blocks like:  **Q5** | title\nMachines: ...\nAnswer: ...
    pattern = re.compile(
        r"\*\*Q(\d+)\*\*\s*\|\s*(.+?)\s*\n"
        r"Machines:\s*(.*?)\s*\n"
        r"Answer:\s*(.*?)(?=\n---|\Z)",
        re.DOTALL,
    )

    for m in pattern.finditer(text):
        qnum     = int(m.group(1))
        title    = m.group(2).strip()
        machines = [
            s.strip().lower()
            for s in m.group(3).split(",")
            if s.strip()
        ]
        entries[qnum] = {"title": title, "machines": machines}

    return entries


def _parse_test_questions(filepath: Path = TEST_QS) -> dict[int, str]:
    """Parse ``test_questions.md`` into ``{q_number: question_text}``."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")

    questions: dict[int, str] = {}
    pattern = re.compile(
        r"\*\*Q(\d+)\*\*\s*\|.*?\n"
        r"Question:\s*(.+?)(?=\n---|\Z)",
        re.DOTALL,
    )

    for m in pattern.finditer(text):
        qnum = int(m.group(1))
        questions[qnum] = m.group(2).strip()

    return questions


# ═════════════════════════════════════════════════════════════════════════════
#  API helpers
# ═════════════════════════════════════════════════════════════════════════════

def _api_retrieve(question: str, top_k: int = 8) -> dict[str, Any]:
    """POST /retrieve and return the JSON response."""
    resp = requests.post(
        f"{API_BASE}/retrieve",
        json={"question": question, "top_k": top_k},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _api_query(question: str) -> dict[str, Any]:
    """POST /query and return the JSON response."""
    resp = requests.post(
        f"{API_BASE}/query",
        json={"question": question},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


# ═════════════════════════════════════════════════════════════════════════════
#  Metrics
# ═════════════════════════════════════════════════════════════════════════════

def _compute_metrics(
    retrieved_sources: set[str],
    expected_machines: list[str],
) -> tuple[float, float, float]:
    """Return ``(recall, precision, f1)``."""
    if not expected_machines:
        # No ground truth → cannot evaluate
        return 0.0, 0.0, 0.0

    expected = {m.lower() for m in expected_machines}
    retrieved = {s.lower() for s in retrieved_sources}

    tp = len(retrieved & expected)

    recall    = tp / len(expected)  if expected  else 0.0
    precision = tp / len(retrieved) if retrieved else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return round(recall, 4), round(precision, 4), round(f1, 4)


# ═════════════════════════════════════════════════════════════════════════════
#  Main
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="HTB RAG evaluator")
    parser.add_argument(
        "--questions", type=str, default=None,
        help="Comma-separated question numbers to evaluate (e.g. 1,6,7)",
    )
    parser.add_argument(
        "--dataset", choices=["v1", "v2"], default="v1",
        help="Dataset version to evaluate (v1 or v2). Default: v1",
    )
    parser.add_argument(
        "--raw-key", action="store_true", default=False,
        help="Use raw uncurated grep answer key (eval/answer_key_raw_grep.md) instead of calibrated canonical benchmark",
    )
    args = parser.parse_args()

    # ── Resolve dataset paths ────────────────────────────────────────────
    if args.dataset == "v2":
        ans_file = (EVAL_DIR / "answer_key_v2_raw_grep.md") if args.raw_key else (EVAL_DIR / "answer_key_v2.md")
        qs_file = EVAL_DIR / "test_questions_v2.md"
        results_out = EVAL_DIR / "results_v2.md"
        answers_out = EVAL_DIR / "answers_generated_v2.md"
    else:
        ans_file = (EVAL_DIR / "answer_key_raw_grep.md") if args.raw_key else ANSWER_KEY
        qs_file = TEST_QS
        results_out = RESULTS_OUT
        answers_out = ANSWERS_OUT

    # ── Parse inputs ─────────────────────────────────────────────────────
    answer_key = _parse_answer_key(ans_file)
    questions  = _parse_test_questions(qs_file)

    if not questions:
        print(f"❌ Could not parse questions from {qs_file.name}")
        sys.exit(1)

    # ── Filter subset if requested ───────────────────────────────────────
    if args.questions:
        subset = {int(q) for q in args.questions.split(",")}
        q_nums = sorted(subset & set(questions.keys()))
    else:
        q_nums = sorted(questions.keys())

    print(f"📝 Evaluating {len(q_nums)} question(s) [dataset: {args.dataset}]…\n")

    # ── Check API health ─────────────────────────────────────────────────
    api_online = False
    in_process_retriever: Any = None
    in_process_synthesizer: Any = None
    try:
        h = requests.get(f"{API_BASE}/health", timeout=3).json()
        api_online = True
        print(f"✅ API online — {h.get('chunks_indexed', '?')} chunks indexed\n")
    except Exception:
        print("ℹ️ API offline at localhost:8000 — initializing resilient in-process pipeline…\n")
        from src.pipeline.retriever import HybridRetriever
        from src.pipeline.synthesizer import Synthesizer
        in_process_retriever = HybridRetriever()
        in_process_synthesizer = Synthesizer()

    # ── Evaluate each question ───────────────────────────────────────────
    rows: list[dict[str, Any]] = []
    generated_answers: list[dict[str, Any]] = []

    for qnum in q_nums:
        q_text = questions[qnum]
        key    = answer_key.get(qnum, {})
        title  = key.get("title", q_text[:40])
        expected_machines = key.get("machines", [])

        print(f"  Q{qnum}: {title}…", end=" ", flush=True)

        # ── Retrieve ─────────────────────────────────────────────────
        raw_res: Any = None
        try:
            if api_online:
                retrieval = _api_retrieve(q_text)
            else:
                if in_process_retriever is None:
                    from src.pipeline.retriever import HybridRetriever
                    in_process_retriever = HybridRetriever()
                raw_res = in_process_retriever.retrieve(q_text)
                retrieval = {
                    "chunks": [c.to_dict() if hasattr(c, "to_dict") else c for c in raw_res.chunks],
                    "manifest": raw_res.manifest,
                    "graph": raw_res.graph_hits,
                }
        except Exception as exc:
            print(f"⚠️ retrieve failed: {exc}")
            rows.append({
                "qnum": qnum, "title": title,
                "recall": 0.0, "precision": 0.0, "f1": 0.0, "sources": [],
            })
            continue

        # Dual-track metrics:
        # 1. Chunk-level metrics: measures exact exploit/procedural precision & lean recall
        result = retrieval
        chunk_sources = {
            c.get("metadata", {}).get("source", "").lower()
            for c in result.get("chunks", [])
            if c.get("metadata", {}).get("source")
        }
        sources = sorted(chunk_sources)
        recall, precision, f1 = _compute_metrics(set(sources), expected_machines)

        # 2. Knowledge Graph Corpus Coverage: measures broad catalog coverage via manifest
        manifest_raw = result.get("manifest") or []
        manifest_sources: set[str] = set()
        if isinstance(manifest_raw, list):
            for m in manifest_raw:
                if isinstance(m, dict) and m.get("machine"):
                    manifest_sources.add(str(m["machine"]).lower())
                elif isinstance(m, str):
                    manifest_sources.add(m.lower())

        corpus_sources = set(sources) | manifest_sources
        corpus_recall, _, _ = _compute_metrics(corpus_sources, expected_machines)

        rows.append({
            "qnum": qnum, "title": title,
            "recall": recall, "precision": precision, "f1": f1,
            "corpus_recall": corpus_recall,
            "sources": sources,
            "manifest_count": len(manifest_sources),
        })

        # ── Synthesize ───────────────────────────────────────────────
        try:
            if api_online:
                synth = _api_query(q_text)
                answer = synth.get("answer", "")
            else:
                if in_process_synthesizer is None:
                    from src.pipeline.synthesizer import Synthesizer
                    in_process_synthesizer = Synthesizer()
                synth = in_process_synthesizer.synthesize(q_text, raw_res or retrieval)
                answer = synth.get("answer", "")
        except Exception as exc:
            answer = f"(synthesis failed: {exc})"

        generated_answers.append({
            "qnum": qnum, "title": title,
            "question": q_text, "answer": answer,
        })

        print(f"Chunk P={precision:.2f}  Chunk R={recall:.2f}  Graph R={corpus_recall:.2f}")
        time.sleep(3.0)

    # ── Write results ────────────────────────────────────────────────────
    _write_results(rows, results_out)

    # ── Write answers ────────────────────────────────────────────────────
    _write_answers(generated_answers, answers_out)

    print(f"\n✅ Done — see {results_out.name} and {answers_out.name}")


# ═════════════════════════════════════════════════════════════════════════════
#  Output writers
# ═════════════════════════════════════════════════════════════════════════════

def _write_results(rows: list[dict[str, Any]], out_path: Path = RESULTS_OUT) -> None:
    """Write evaluation results markdown with a summary table."""
    lines: list[str] = [
        "# HTB RAG – Evaluation Results (Dual-Track Evaluation)\n",
        "> **Dual-Track Methodology:**",
        "> - **Chunk Precision & Recall:** Computed strictly on authentic retrieved chunks (top-k = 5–8) to evaluate procedure accuracy without context bloat.",
        "> - **Graph Corpus Recall:** Evaluates overall catalogue coverage provided by the Knowledge Graph Manifest table for broad queries.\n",
        "| Q# | Question (short) | Chunk P | Chunk R | Graph R | Chunks | Sources Found |",
        "|----|-----------------|---------|---------|---------|--------|---------------|",
    ]

    total_recall = 0.0
    total_precision = 0.0
    total_corpus_recall = 0.0
    total_f1 = 0.0
    n = len(rows) or 1

    for r in rows:
        src_str = ", ".join(r["sources"][:6]) or "—"
        if len(r["sources"]) > 6:
            src_str += f" (+{len(r['sources']) - 6} more)"
        lines.append(
            f"| {r['qnum']:<2} "
            f"| {r['title'][:30]:<30} "
            f"| {r['precision']:.2f}    "
            f"| {r['recall']:.2f}    "
            f"| {r.get('corpus_recall', r['recall']):.2f}    "
            f"| {len(r['sources']):<6} "
            f"| {src_str} |"
        )
        total_recall += r["recall"]
        total_precision += r["precision"]
        total_corpus_recall += r.get("corpus_recall", r["recall"])
        total_f1 += r.get("f1", 0.0)

    avg_r = total_recall / n
    avg_p = total_precision / n
    avg_cr = total_corpus_recall / n
    avg_f1 = total_f1 / n

    lines.append("")
    lines.append(f"**Chunk Precision: {avg_p:.2f}** | **Chunk Recall: {avg_r:.2f}** | **Corpus Graph Recall: {avg_cr:.2f}** | **Average F1: {avg_f1:.2f}**")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📊 Chunk Precision: {avg_p:.2f} | Chunk Recall: {avg_r:.2f} | Corpus Graph Recall: {avg_cr:.2f} | Avg F1: {avg_f1:.2f}")


def _write_answers(answers: list[dict[str, Any]], out_path: Path = ANSWERS_OUT) -> None:
    """Write synthesized answers markdown."""
    lines: list[str] = [
        "# HTB RAG – Generated Answers\n",
        "Auto-generated by `evaluator.py` for manual review.\n",
    ]

    for a in answers:
        lines.append(f"---\n")
        lines.append(f"## Q{a['qnum']} — {a['title']}\n")
        lines.append(f"**Question:** {a['question']}\n")
        lines.append(f"**Answer:**\n")
        lines.append(f"{a['answer']}\n")

    out_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

