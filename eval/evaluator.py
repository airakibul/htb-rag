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
ANSWER_KEY    = EVAL_DIR / "answer_key.md"
TEST_QS       = EVAL_DIR / "test_questions.md"
RESULTS_OUT   = EVAL_DIR / "results.md"
ANSWERS_OUT   = EVAL_DIR / "answers_generated.md"
API_BASE      = "http://127.0.0.1:8000"


# ═════════════════════════════════════════════════════════════════════════════
#  Answer-key parser
# ═════════════════════════════════════════════════════════════════════════════

def _parse_answer_key() -> dict[int, dict[str, Any]]:
    """Parse ``answer_key.md`` into ``{q_number: {title, machines}}``."""
    text = ANSWER_KEY.read_text(encoding="utf-8", errors="ignore")

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


def _parse_test_questions() -> dict[int, str]:
    """Parse ``test_questions.md`` into ``{q_number: question_text}``."""
    text = TEST_QS.read_text(encoding="utf-8", errors="ignore")

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
) -> tuple[float, float]:
    """Return ``(recall, precision)``."""
    if not expected_machines:
        # No ground truth → cannot evaluate
        return 0.0, 0.0

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
    args = parser.parse_args()

    # ── Parse inputs ─────────────────────────────────────────────────────
    answer_key = _parse_answer_key()
    questions  = _parse_test_questions()

    if not questions:
        print("❌ Could not parse test_questions.md")
        sys.exit(1)

    # ── Filter subset if requested ───────────────────────────────────────
    if args.questions:
        subset = {int(q) for q in args.questions.split(",")}
        q_nums = sorted(subset & set(questions.keys()))
    else:
        q_nums = sorted(questions.keys())

    print(f"📝 Evaluating {len(q_nums)} question(s)…\n")

    # ── Check API health ─────────────────────────────────────────────────
    try:
        h = requests.get(f"{API_BASE}/health", timeout=5).json()
        print(f"✅ API online — {h.get('chunks_indexed', '?')} chunks indexed\n")
    except Exception:
        print("❌ Cannot reach API at localhost:8000. Is it running?")
        sys.exit(1)

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
        try:
            retrieval = _api_retrieve(q_text)
        except Exception as exc:
            print(f"⚠️ retrieve failed: {exc}")
            rows.append({
                "qnum": qnum, "title": title,
                "recall": 0.0, "precision": 0.0, "sources": [],
            })
            continue

        # Collect unique sources from retrieved chunks
        chunks  = retrieval.get("chunks", [])
        sources = sorted({
            c.get("metadata", {}).get("source", "")
            for c in chunks
            if c.get("metadata", {}).get("source")
        })

        recall, precision, f1 = _compute_metrics(set(sources), expected_machines)

        rows.append({
            "qnum": qnum, "title": title,
            "recall": recall, "precision": precision, "f1": f1,
            "sources": sources,
        })

        # ── Synthesize ───────────────────────────────────────────────
        try:
            synth = _api_query(q_text)
            answer = synth.get("answer", "")
        except Exception as exc:
            answer = f"(synthesis failed: {exc})"

        generated_answers.append({
            "qnum": qnum, "title": title,
            "question": q_text, "answer": answer,
        })

        print(f"R={recall:.2f}  P={precision:.2f}  F1={f1:.2f}")

    # ── Write results.md ─────────────────────────────────────────────────
    _write_results(rows)

    # ── Write answers_generated.md ───────────────────────────────────────
    _write_answers(generated_answers)

    print(f"\n✅ Done — see {RESULTS_OUT.name} and {ANSWERS_OUT.name}")


# ═════════════════════════════════════════════════════════════════════════════
#  Output writers
# ═════════════════════════════════════════════════════════════════════════════

def _write_results(rows: list[dict[str, Any]]) -> None:
    """Write ``eval/results.md`` with a summary table."""
    lines: list[str] = [
        "# HTB RAG – Evaluation Results\n",
        "| Q# | Question (short) | Recall | Precision | Sources Found |",
        "|----|-----------------|--------|-----------|---------------|",
    ]

    total_recall = 0.0
    total_precision = 0.0
    n = len(rows) or 1

    for r in rows:
        src_str = ", ".join(r["sources"][:6]) or "—"
        lines.append(
            f"| {r['qnum']:<2} "
            f"| {r['title'][:30]:<30} "
            f"| {r['recall']:.2f}   "
            f"| {r['precision']:.2f}      "
            f"| {src_str} |"
        )
        total_recall += r["recall"]
        total_precision += r["precision"]

    avg_r = total_recall / n
    avg_p = total_precision / n

    lines.append("")
    lines.append(f"**Average Recall: {avg_r:.2f}** | **Average Precision: {avg_p:.2f}**")
    lines.append("")

    RESULTS_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📊 Avg Recall: {avg_r:.2f} | Avg Precision: {avg_p:.2f}")


def _write_answers(answers: list[dict[str, Any]]) -> None:
    """Write ``eval/answers_generated.md`` with all synthesized answers."""
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

    ANSWERS_OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
