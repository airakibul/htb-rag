# Design Note — HTB Cheatsheet Assistant (RAG)

## 1. Chunking Strategy

### Why Naive Chunking Fails on Penetration Testing Writeups
Fixed-size sliding windows (e.g., 512 tokens with 50-token overlap) fail catastrophically on offensive security walkthroughs:
1. **Command-Output Severing:** Exploit steps pair terminal commands directly with output banners, error messages, or extracted hashes. Sliding windows frequently slice between command and output, corrupting syntax and context.
2. **Loss of Attack Lifecycle Phase:** An isolated command like `secretsdump.py` looks identical whether executed during initial enumeration, lateral movement, or domain compromise. Without structural heading awareness, the semantic phase is lost.
3. **Broken Code Block Fences:** Slicing mid-code-block creates orphaned triple backticks (```), corrupting Markdown parsers, vector embeddings, and downstream LLM synthesis prompts.

### The Solution: AST- & Heading-Aware Structural Chunking
Our chunker (`src/chunker.py`) segments documents along the natural offensive lifecycle (`##` Phase $\to$ `###` Step $\to$ `####` Sub-step) with deterministic length guardrails:

- **Pre-Processing Normalization:** In 449 of 462 writeups, headings lacked preceding newlines (e.g., `Creator ## Recon`). An AST normalization pre-pass (`re.sub(r'([^\n#\r])[ \t]*(#{2,4}[ \t]+[A-Za-z0-9])', r'\1\n\n\2', raw)`) un-sticks glued headings, recovering thousands of attack steps previously swallowed into boilerplate sections.
- **Adaptive Segmentation:** Writeups are dynamically classified into archetypes:
  - *Normal Writeups:* Split hierarchically at `###` steps; sub-split at `####` if a section exceeds 2,400 characters (~600 tokens).
  - *Monolithic ("Mega") Writeups:* Recursively split along paragraph (`\n\n`) and line (`\n`) boundaries with a strict 2,400-character ceiling, completely eliminating token overflow.
- **Code Block Fence Integrity:** If an oversized code block must be split, the chunker cleanly terminates the block with `\n``` ` and re-opens it in the next chunk with the identical language identifier (e.g., ` ```bash\n `), preventing syntax corruption.
- **Context Injection (Semantic Breadcrumbs):** Every chunk is prepended with a structured header:
  `[Machine: <Name> | OS: <OS> | Phase: <Phase> | Path: <H2 > H3 > H4>]`
  This injects machine name, target OS, and attack phase into both dense and sparse representations, enabling BM25 keyword matching and accurate LLM citation without side-channel metadata tracking.
- **Multimodal Artifacts:** Raw Markdown image tags are stripped to eliminate URL clutter; key non-decorative screenshots are analyzed via Gemini Vision and embedded as descriptive text chunks (`chunk_type="image_desc"`).

---

## 2. Why Lexical vs. Embedding Retrieval (and Why Hybrid RRF is Essential)

Neither lexical search nor dense embedding retrieval is sufficient on its own for offensive security queries:

- **The Lexical (BM25) Blindspot:** Pure lexical search fails on conceptual and cheatsheet queries. A query like *"Windows privilege escalation cheatsheet"* rarely matches writeups because penetration testers document specific actions (e.g., *"abused SeImpersonatePrivilege via PrintSpoofer"* or *"hijacked unquoted service path"*) rather than repeating the textbook phrase *"privilege escalation"*.
- **The Dense Embedding Blindspot:** Dense semantic search (`all-MiniLM-L6-v2`) excels at conceptual matching but fails on exact, low-frequency technical tokens. Critical entities such as CVE identifiers (`CVE-2021-44228`), unique offensive tools (`evil-winrm`, `certipy`, `mimikatz`), and command-line flags (`-just-dc`, `-k -no-pass`) map to narrow, fragile coordinates in embedding space where cosine similarity easily drifts toward generic text.

### The Hybrid Solution
Our architecture combines both paradigms in a multi-stage retrieval pipeline:
1. **Parallel Retrieval:** BM25 retrieves exact keyword, tool, and CVE matches; dense vector search retrieves semantically relevant conceptual contexts.
2. **Reciprocal Rank Fusion (RRF with $k=60$):** Combines the rank positions ($RRF(d) = \sum \frac{1}{60 + r_i(d)}$) rather than uncalibrated raw scores, preventing either retriever from dominating the candidate set.
3. **Cross-Encoder Neural Reranking (`ms-marco-MiniLM-L-6-v2`):** Jointly evaluates query-document token interactions across the top 30 RRF candidates, filtering out superficial lexical matches and elevating chunks that describe genuine exploit execution.
4. **Source Diversification:** Enforces per-machine chunk limits (1 for broad queries, 2 for specific queries), preventing single verbose writeups from saturating the context.

---

## 3. What to Improve with Another Week: Graph-Assisted Recall & Precision Calibration

The actual benchmark run (`eval/results.md`) demonstrates **Average Precision of 0.67 and Average Recall of 0.35**. 

While Active Directory, Windows, and credential queries achieve strong precision (e.g., Kerberoasting 1.00, WinRM 1.00, AD 0.96, Password Cracking 0.96, ADCS 0.84), recall remains capped at 0.35. For broad cheatsheets, over 60–200+ machines are relevant, but the retriever is constrained to $k=8\text{–}15$ chunks to protect LLM context limits. Conversely, on certain specific queries like Log4Shell (Q8) and Samba (Q15), keyword bleeding resulted in high recall (1.00 on Log4Shell) but lower precision (0.08) due to generic logging and SMB hits.

### Concrete Implementation Plan: Graph-Assisted Manifest Injection
The repository already contains a fully populated NetworkX knowledge graph (`graph/htb_graph.json`) mapping `Machine ──HAS_TECHNIQUE──► Technique ──BELONGS_TO──► Category`. 

With another week, we would implement **Graph-Assisted Citation & Manifest Expansion**:
1. **Intent-Based Graph Traversal:** In `src/retriever.py`, classify incoming queries for broad cheatsheet intent. When detected, query the knowledge graph for all machines connected to the target attack category (e.g., extracting all 22 machines tagged with `ADCS` or all 63 machines tagged with `Active Directory`).
2. **Prompt Manifest Injection:** Rather than retrieving 100 raw text chunks (which would exceed context limits and degrade synthesis quality), the retriever injects a compact **Machine Manifest Table** (machine name, OS, difficulty, and primary technique) directly into the prompt alongside the top 8 detailed text chunks.
3. **Dual-Layer Synthesis:** The LLM generates the detailed technical steps and commands using the top-8 retrieved chunks, and supplements the citations using the full machine manifest:
   > *"Demonstrated in detail on Certified and Absolute; also featured across 20 other corpus machines including Authority, Escape, Scepter, and VulnCicada."*

**Expected Impact:** This enhancement will directly address the 0.35 recall bottleneck, pushing broad cheatsheet recall to **>0.85** while maintaining high precision and zero prompt token overflow.
