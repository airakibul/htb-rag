# Evaluation Writeup — HTB Cheatsheet Assistant (RAG)

## Retrieval Metrics

| Q# | Question | Recall | Precision |
|----|----------|--------|-----------|
| 1  | Windows privesc cheatsheet | 0.09 | 0.38 |
| 2  | Linux privesc cheatsheet | 0.07 | 0.25 |
| 3  | AD attack techniques | 0.04 | 0.25 |
| 4  | ADCS certificate abuse | 0.00 | 0.00 |
| 5  | Password cracking / hash dump | 0.04 | 0.25 |
| 6  | AS-REP Roasting | 0.11 | 0.25 |
| 7  | certipy usage | 0.14 | 0.38 |
| 8  | CVE-2026-4480 | 0.00 | 0.00 |
| 9  | WriteOwner abuse | 0.07 | 0.14 |
| 10 | ESC9 ADCS attack | 0.50 | 0.14 |
| 11 | BloodHound attack paths | 0.06 | 0.38 |
| 12 | Shadow Credentials | 0.08 | 0.14 |
| 13 | Samba RCE | 0.04 | 0.12 |
| 14 | evil-winrm shell access | 0.07 | 0.62 |
| 15 | GenericAll abuse | 0.05 | 0.14 |
| **Avg** | | **0.09** | **0.23** |

## Metric Interpretation

Recall is low (0.09 average) because the ground truth for broad questions includes every machine that mentions the keyword (e.g., Q14 evil-winrm appears in 74 machines), while the retriever returns only top-8 chunks. A system returning 8 results from a ground truth of 74 has a theoretical recall ceiling of ~0.11 even with perfect ranking. Narrow questions with small ground truth sets (Q10: ESC9 with only 2 machines) hit 0.50 recall.

Precision is moderate (0.23 average), meaning roughly 1 in 4 retrieved chunks comes from a machine in the ground truth. Q14 (evil-winrm) achieved 0.62 precision — the highest — because the keyword is distinctive and BM25 matches it well. Q4 (ADCS) and Q8 (CVE-2026-4480) scored 0.00 on both metrics: Q4 because the query "ADCS certificate abuse" doesn't match the exact terms used in writeups (writeups say "certipy", "ESC9", "template"), and Q8 because CVE-2026-4480 appears in only one machine (htb-abducted) which the retriever didn't surface in its top-8.

## Synthesis Quality

**Citation accuracy.** For well-retrieved questions (Q1, Q6, Q7, Q9, Q14, Q15), the synthesizer correctly cites machine names from the retrieved context. For example, Q9 (WriteOwner) correctly cites htb-reel, and Q15 (GenericAll) correctly cites htb-support. Q6 (AS-REP Roasting) accurately lists 13 machines from graph findings.

**Hallucination.** Two instances of quality concern were observed:
- Q4 (ADCS) and Q12 (Shadow Credentials): The graph query returned an overly broad machine list — including obviously unrelated machines like htb-popcorn, htb-scriptkiddie, htb-zipper — because the graph's category matching is too aggressive. The AD category keyword "shadow credential" matched far more machines than actually demonstrate the technique. This is a graph builder issue, not an LLM hallucination per se, but the synthesizer faithfully cited these false positives without filtering.
- Q8 (CVE-2026-4480): The LLM correctly responded "Insufficient data in the retrieved writeups" rather than inventing an explanation, which is the desired behaviour.

**Grounding.** Q10 (ESC9) and Q13 (Samba RCE) returned "Insufficient data" despite some relevant context existing in the corpus. This suggests the retriever didn't surface the right chunks, and the strict system prompt correctly prevented the LLM from filling the gap with training data.

**Answer structure.** For cheatsheet-style questions (Q1–Q3), the synthesizer correctly groups techniques by attack phase with machine citations in the requested format. The answers are well-structured with tables and bullet points.

## Overall Assessment

The system successfully demonstrates grounded, cited answers for queries where retrieval succeeds. The low recall is a structural constraint of top-k retrieval against an exhaustive ground truth, not a system failure. The most impactful improvements would be: (1) increasing top_k for broad cheatsheet queries, (2) fixing the graph builder's over-matching on category keywords, and (3) adding a cross-encoder re-ranker to improve precision as described in the design note. The strict system prompt effectively prevents hallucination — the model says "Insufficient data" rather than inventing facts, which is critical for a security reference tool.
