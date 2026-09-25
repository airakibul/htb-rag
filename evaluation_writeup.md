# Evaluation Writeup — HTB Cheatsheet Assistant (RAG)

## Retrieval Metrics (Current Test Set — 15 Questions)

| Q# | Question (short) | Precision | Recall | Sources Found |
|----|-----------------|-----------|--------|---------------|
| 1  | Windows privesc cheatsheet | 0.93 | 0.12 | htb-blazorized, htb-bounty, htb-bruno, htb-cereal, htb-darkzero, htb-devel |
| 2  | Linux privesc cheatsheet | 0.87 | 0.05 | htb-artificial, htb-bigbang, htb-brainfuck, htb-cache, htb-crossfittwo, htb-cybermonday |
| 3  | AD attack techniques | 0.93 | 0.22 | htb-active, htb-administrator, htb-authority, htb-certified, htb-cicada, htb-darkzero |
| 4  | ADCS certificate abuse | 1.00 | 0.18 | htb-certified, htb-escape, htb-mirage, htb-mist |
| 5  | Password cracking / hash dump | 1.00 | 0.06 | htb-awkward, htb-blazorized, htb-breach, htb-cat, htb-compiled, htb-craft |
| 6  | Kerberoasting | 1.00 | 0.15 | htb-active, htb-rebound, htb-sizzle, htb-tombwatcher |
| 7  | MS17-010 EternalBlue | 1.00 | 1.00 | htb-blue, htb-legacy |
| 8  | CVE-2021-44228 Log4Shell | 1.00 | 0.50 | htb-crafty |
| 9  | SQL injection with sqlmap | 0.40 | 0.13 | htb-charon, htb-crossfittwo, htb-enterprise, htb-shared, htb-whiterabbit |
| 10 | Docker container breakout | 0.60 | 0.60 | htb-ariekei, htb-artificial, htb-carpediem, htb-cybermonday, htb-data, htb-extension |
| 11 | JuicyPotato / PrintSpoofer | 0.50 | 0.15 | htb-pivotapi, htb-rainbow, htb-tally, htb-vulnescape |
| 12 | DCSync attack | 1.00 | 0.22 | htb-delegate, htb-forest, htb-sauna, htb-sizzle |
| 13 | SUID / GTFOBins privesc | 0.33 | 0.17 | htb-charon, htb-flujab, htb-forwardslash, htb-knife, htb-laboratory, htb-magic |
| 14 | WinRM / evil-winrm | 1.00 | 0.07 | htb-driver, htb-manager, htb-puppy, htb-resolute, htb-support |
| 15 | Samba RCE | 1.00 | 0.08 | htb-abducted, htb-lame |
| **Avg** | | **0.84** | **0.25** | |

---

## Precision vs. Recall Analysis

**Precision (0.84 avg):** High precision means that when the system retrieves a chunk, it is almost always from a relevant machine. 8 out of 15 questions achieve perfect precision (1.00), and no question drops below 0.33. The technique-specific discriminative filters and source diversification contribute directly to this — irrelevant chunks are filtered before they reach the synthesizer.

**Recall (0.25 avg):** Recall is the main weakness. Broad cheatsheet questions (Q1, Q2, Q5) have very low recall (0.05–0.12) because the answer key expects 100–230+ machines while the retriever returns at most 15 diversified sources. Specific queries perform better — Q7 (EternalBlue) achieves perfect recall (1.00), and Q10 (Docker breakout) reaches 0.60. The gap is architectural: the system retrieves the *best* chunks rather than *all* relevant ones, which is the correct trade-off for answer quality but limits source coverage metrics.

**Perfect Precision Questions (P=1.0):** Q4 (ADCS), Q5 (hash dump), Q6 (Kerberoasting), Q7 (EternalBlue), Q8 (Log4Shell), Q12 (DCSync), Q14 (WinRM), Q15 (Samba RCE) — 8 out of 15 questions return only relevant machines.

---

## Architectural Iteration Summary

| Phase | Avg Precision | Avg Recall | Key Change |
|-------|--------------|------------|------------|
| Phase 0 (Baseline) | 0.23 | 0.09 | Naive chunking, BM25 only |
| Phase 2 | 0.54 | 0.25 | Fixed stuck headings, added vector search |
| Phase 3 | 0.66 | 0.31 | OS detection fix, hybrid RRF fusion |
| Phase 4 | 0.84 | 0.25 | Cross-encoder reranking, technique filters, source diversification |
| **Total Gain** | **+265% (3.7×)** | **+178% (2.8×)** | |

---

## Root Cause Breakdown & What Fixed Them

### 1. The 97% "Stuck Heading" Bug
- **Bug:** In 449 of 462 writeups, headings lacked preceding newlines (e.g. `18d 22:54:36 Creator ## Recon`). Because the split regex required `^##\s+`, all recon and exploit sections fell under `## Box Info` and were deleted by `IGNORE_HEADINGS`.
- **Fix:** Applied pre-processing normalization `re.sub(r'([^\n])\s*(#{2,4}\s+[A-Za-z0-9])', r'\1\n\n\2', raw)` before chunking. This recovered thousands of missing attack step sections.

### 2. The 1.2M Character "Monster Chunk" Anomaly
- **Bug:** Writeups with long walkthrough sections and sparse subheadings generated chunks up to 1,200,000 characters, exceeding Gemini's token window and destroying vector embedding fidelity.
- **Fix:** Implemented a recursive, line-and-paragraph-aware sub-splitter in `src/chunker.py` (`_split_into_paragraphs`) enforcing a strict ~2,400 character ceiling per chunk.

### 3. The 85% "Unknown OS" Tagging Defect
- **Bug:** `_clean(raw)` deleted markdown images (`![Linux](/icons/Linux.webp)`) *before* `_parse_box_info` parsed the OS. As a result, 9,215 of 10,833 chunks were tagged `os: "unknown"`, causing OS filters to discard valid candidates.
- **Fix:** Added fallback OS detection directly on `raw[:4000]` before stripping image links. Known OS coverage jumped from 15% to 98.7%.

### 4. Machine Source Diversification
- **Bug:** Without per-machine caps, 6 out of 8 retrieved chunks for broad cheatsheets came from a single verbose machine, destroying diversity.
- **Fix:** Enforced a maximum of 1 chunk per machine for broad queries and 2 chunks for specific queries in `src/retriever.py`.

---

## Synthesis Quality & Grounding

- **Strict Grounding:** The synthesizer uses a strict system prompt requiring all claims to come from retrieved context. Answers contain no hallucinated CVE numbers, fabricated credentials, or invented machine names.
- **Machine Citations:** Every technique in generated answers includes explicit machine attribution in the format `(seen on: MachineName)`.
- **Structured Output:** Cheatsheet answers (Q1–Q3) follow the offensive security lifecycle: Recon → Foothold → Lateral Movement → Privilege Escalation.
- **Graceful Degradation:** When context is insufficient, the system responds with "Insufficient data in the retrieved writeups" rather than generating unsupported claims.
- **No Truncation:** All 15 generated answers in `eval/answers_generated.md` are complete and well-formed.
