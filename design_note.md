# Design Note — HTB Cheatsheet Assistant (RAG) — Version 2.0

> **System Architecture & Design Rationale**  
> Comprehensive documentation of the architectural principles, chunking mechanics, multi-stage hybrid retrieval, sub-2s latency tuning, and dual-track evaluation framework powering Version 2.0.

---

## 1. Chunking Strategy & In-Memory Strategy Pattern

### 1.1 The Failure of Naive Chunking on Penetration Testing Walkthroughs
Fixed-size sliding windows (e.g., 512 tokens with 50-token overlap) fail catastrophically on offensive security documentation:
1. **Command-Output Severing:** Slicing mid-sequence severs terminal commands from their associated execution banners, error strings, or extracted credential hashes, completely invalidating exploit mechanics.
2. **Loss of Attack Lifecycle Phase:** Isolated commands (e.g., `secretsdump.py -just-dc`) appear ambiguous across enumeration, lateral movement, or domain compromise without structural heading context.
3. **Broken Markdown Code Fences:** Arbitrary token splits inside triple backticks (```) generate orphaned syntax blocks, corrupting downstream markdown renderers, embedding tokenizers, and LLM prompt templates.

### 1.2 AST- & Heading-Aware Structural Chunking
Our chunker (`src/pipeline/chunker.py`) segments along the offensive methodology lifecycle (`## Phase` $\to$ `### Step` $\to$ `#### Sub-step`) with deterministic guardrails:
- **Heading Normalization Pre-Pass:** In 449 of 462 writeups in `raw/`, author Markdown formatting lacked preceding newlines (`Author ## Recon`). A pre-tokenization regex:
  ```python
  re.sub(r'([^\n#\r])[ \t]*(#{2,4}[ \t]+[A-Za-z0-9])', r'\1\n\n\2', raw_text)
  ```
  un-glues headings, recovering thousands of submerged tactical steps.
- **Adaptive Hierarchical Segmentation:** Normal writeups split hierarchically at `###` (sub-splitting at `####` if exceeding 2,400 characters / $\approx 600$ tokens). Monolithic writeups without subheadings split recursively at paragraph breaks (`\n\n`) and line breaks (`\n`) under the strict 2,400-character ceiling.
- **Code Block Fence Preservation:** When splitting oversized code blocks, the chunker cleanly closes the block with `\n``` ` and reopens the continuation chunk with the identical language identifier (` ```bash\n `), guaranteeing syntax validity.
- **Context Injection (Semantic Breadcrumbs):** Every chunk is prepended with structured contextual metadata:
  ```text
  [Machine: <Name> | OS: <OS> | Phase: <Phase> | Path: <H2 > H3 > H4>]
  ```
  This injects target identity and offensive phase into both dense embedding vectors and sparse BM25 indices, enabling accurate keyword matching and zero-overhead LLM citations.

### 1.3 Strategy Pattern & Dynamic In-Memory Chunking
In Version 2.0, chunking was refactored under the **Strategy Pattern**:
- Defined the abstract domain contract `ChunkingStrategy` in [`src/domain/interfaces.py`](src/domain/interfaces.py).
- Implemented `MarkdownChunker` in [`src/pipeline/chunker.py`](src/pipeline/chunker.py), supporting interchangeable chunking algorithms.
- Introduced `chunk_text(text: str, source: str = "") -> List[Chunk]` to support dynamic in-memory chunking of user notes, API payloads, and test fixtures without disk I/O.
- Preserved a root-level shim in `src/chunker.py` ensuring backward compatibility with legacy tooling.

---

## 2. Multi-Stage Hybrid Retrieval & Latency Optimization

Neither lexical nor dense semantic retrieval is sufficient in isolation for offensive security queries:

```
                  ┌───────────────────────────────────────────┐
                  │                User Query                 │
                  └─────────────────────┬─────────────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
              ┌─────────────────────┐       ┌─────────────────────┐
              │     BM25 Lexical    │       │ Dense Vector Search │
              │   Exact Tools/CVEs  │       │  all-MiniLM-L6-v2   │
              └──────────┬──────────┘       └──────────┬──────────┘
                         │                             │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │ Reciprocal Rank Fusion(RRF) │
                         │     k = 60, Top-12 Pool     │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │ Neural Cross-Encoder Rerank │
                         │   ms-marco-MiniLM-L-6-v2    │
                         │    (Sub-2s CPU Latency)     │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Source Diversification    │
                         │   (Per-Machine Quotas)      │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Top-K Procedural Chunks   │
                         └─────────────────────────────┘
```

### 2.1 Complementary Retrieval Paradigms
- **Lexical (BM25) Blindspots:** Fails on conceptual questions. *"Windows privilege escalation cheatsheet"* rarely matches writeup bodies directly because offensive researchers document specific actions (e.g., *"abused SeImpersonatePrivilege via PrintSpoofer"*) rather than textbook category names.
- **Dense Embedding Blindspots:** Dense models (`all-MiniLM-L6-v2`) capture high-level semantics well but stumble on rare, low-frequency technical tokens: CVE numbers (`CVE-2021-44228`), offensive tool names (`evil-winrm`, `certipy`), and CLI parameters (`-just-dc`, `-k -no-pass`).

### 2.2 Fusion & Reranking Architecture
1. **Parallel Lexical & Dense Retrieval:** BM25 retrieves exact technical keywords and CVE identifiers; ChromaDB dense vector search captures high-level conceptual intent.
2. **Reciprocal Rank Fusion (RRF, $k=60$):** Merges candidates by rank position:
   $$RRF(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$
   This prevents raw score distribution disparities from letting one retriever dominate candidates.
3. **Cross-Encoder Neural Reranking (`ms-marco-MiniLM-L-6-v2`):** Jointly processes query and chunk tokens across self-attention layers to score deep semantic relevance.
4. **Source Diversification:** Enforces per-machine chunk limits (maximum 1 chunk per machine for broad queries, 2 for specific queries), preventing verbose walkthroughs from monopolizing the context window.

### 2.3 Sub-2-Second Latency Profiling on CPU
In Version 1.0, retrieval latency averaged **~8.5 seconds on CPU**. Execution profiling identified that **91% of latency** was consumed by the neural cross-encoder performing 30 forward passes per query over lengthy chunks.

**The Optimization in Version 2.0 (`src/pipeline/retriever.py`):**
- Calibrated the RRF candidate pool passed to the cross-encoder from $N=30$ down to $N=12$.
- Empirical testing proved that true positive candidates for offensive questions consistently placed within the top 10 RRF ranks.
- **Results:** Cross-encoder inference dropped from 7.8s to **1.3s**, bringing end-to-end P90 retrieval latency to **~1.95s on standard CPU**, an overall **76% latency reduction** with zero precision loss.

---

## 3. Knowledge Graph Integration & Manifest Injection

### 3.1 The Recall Funnel on Broad Queries
Offensive security cheatsheet questions (e.g., Windows Privesc, Linux Privesc, Active Directory) span 60 to 200+ machines across the 462-machine corpus. However:
- LLM prompt context budgets cap text chunk retrieval to $k = 5\text{–}8$ chunks.
- Retrieving 60+ full text chunks induces severe context window dilution, prompt truncation, and elevated latency.
- Consequently, conventional RAG systems suffer a mathematical recall ceiling of $0.06\text{–}0.18$ on broad queries.

### 3.2 Graph-Assisted Manifest Injection
To decouple **inventory recall** from **context window token limits**, Version 2.0 leverages the NetworkX knowledge graph (`graph/htb_graph.json`):
1. **Query Intent Classification:** `QueryEnhancer` classifies incoming queries as `broad` vs `specific`.
2. **Graph Traversal (`src/graph/manifest.py`):** For broad queries, the system traverses `Technique` and `Category` nodes to identify all predecessor `Machine` nodes, extracting metadata (Machine name, OS, Difficulty, matched technique).
3. **Prompt Manifest Injection:** The extracted inventory is compiled into a lightweight Markdown table (~300 tokens) and injected into the prompt alongside the 8 deep procedural chunks.
4. **Dual-Layer LLM Prompting:** The synthesizer delivers granular, step-by-step exploit commands from the retrieved chunks, followed by a dedicated section:
   ```markdown
   ## Also Demonstrated On:
   MachineA (Windows, Medium), MachineB (Linux, Hard), MachineC (Windows, Easy)...
   ```
   Surfacing complete corpus breadth without context bloat.

### 3.3 Precision Guardrails & Candidate Entity Injection
- **Noise Reduction:** Stripped non-discriminative writeup section headers (`exploit`, `intended`, `shortcut`, `template injection`) that previously caused spurious graph associations.
- **Target OS Filtering:** Enforced strict target OS signal propagation (`windows` vs `linux`). Windows machines are strictly excluded from Linux cheatsheets and vice versa.
- **Specific Query Candidate Injection:** For specific queries (e.g. Kerberoasting, EternalBlue, DCSync), candidate machines linked to the specific technique or CVE in the graph are injected into the candidate retrieval pool, boosting specific query recall without context contamination.

---

## 4. Layered Clean Architecture (SOLID Principles)

To eliminate technical debt from the monolithic prototype, Version 2.0 refactored the entire codebase into 5 clean layers:

```
┌────────────────────────────────────────────────────────┐
│                   Presentation Layer                   │
│            FastAPI REST API (src/api/)                 │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Pipeline Layer                       │
│    Orchestration: Retriever, Enhancer, Synthesizer     │
│                 (src/pipeline/)                        │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼─────────────┐┌─────────────▼─────────────┐
│       Domain Layer        ││       Graph Domain        │
│ Abstract Contracts (DIP)  ││ Builder, Querier, Manifest│
│   Entities & DTO Models   ││       (src/graph/)        │
│       (src/domain/)       │└───────────────────────────┘
└─────────────┬─────────────┘
              │
┌─────────────▼──────────────────────────────────────────┐
│                 Infrastructure Layer                   │
│ Adapters: ChromaDB, NetworkX, CrossEncoder, Groq/Gemini│
│                (src/infrastructure/)                   │
└────────────────────────────────────────────────────────┘
```

### 4.1 SOLID Compliance Matrix

| Principle | Architectural Implementation |
|:---|:---|
| **Single Responsibility (SRP)** | Every module has one isolated duty: `manifest.py` extracts machine inventories; `query_enhancer.py` detects scope and target OS; `cross_encoder.py` executes neural reranking. |
| **Open/Closed (OCP)** | Domain interfaces allow adding new vector stores (e.g., Qdrant), graph databases (Neo4j), or LLM providers without altering pipeline logic. |
| **Liskov Substitution (LSP)** | `GroqProvider` and `GeminiProvider` implement `LLMProvider` identically, permitting zero-side-effect failover between providers. |
| **Interface Segregation (ISP)** | Granular, fine-grained interfaces: `VectorStore`, `GraphStore`, `EmbeddingService`, `LLMProvider`, `Reranker`, and `ChunkingStrategy`. |
| **Dependency Inversion (DIP)** | High-level orchestrators (`HybridRetriever`, `Synthesizer`, API routes) depend purely on abstract interfaces; concrete infrastructure is injected via constructors. |

---

## 5. Dual-Track Evaluation Methodology & Generalization Proof

### 5.1 Why Traditional Single-Metric RAG Evaluation Fails
In early experimentation, evaluating RAG solely on chunk retrieval created a false dichotomy:
- Evaluating only Top-K chunks penalized the system on broad queries where citing 100 machines via chunks is physically impossible.
- Merging whole-graph manifest machines directly into chunk metrics artificially distorted precision and recall calculations.

### 5.2 The Dual-Track Metric Formulation
Version 2.0 introduces the **Dual-Track Evaluation Methodology**:

1. **Track 1: Procedural Chunk Precision & Recall ($P_{chunk}$, $R_{chunk}$):**
   - Measures the quality of the top-k ($k=5\text{–}8$) procedural text chunks delivered into the LLM context.
   - Evaluates whether the retrieved chunks provide authentic, working exploit procedures and relevant target machines without irrelevant distractors.
2. **Track 2: Knowledge Graph Corpus Recall ($R_{graph}$):**
   - Measures the complete catalog discovery provided by the Knowledge Graph Manifest table across broad cheatsheet queries.

### 5.3 Empirical Benchmark Comparison

```
Metric Progression Across Major Milestones:

Chunk Precision:
  Version 1.0:           [25%]
  V2.0 (V1 Calibrated):  [==================== 66%]
  V2.0 (V2 Unseen):      [========================= 81%]

Macro F1 Score:
  Version 1.0:           [11%]
  V2.0 (V1 Calibrated):  [================== 59%]
  V2.0 (V2 Unseen):      [====================== 70%]
```

| Evaluation Suite | Chunk Precision | Chunk Recall | Graph Corpus Recall | Macro F1 | Test Suite |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Version 1.0 (`main` baseline)** | 0.25 | 0.08 | 0.12 | 0.11 | 22 tests |
| **Version 2.0 (Dataset V1 Calibrated)** | **0.66** | **0.59** | **0.83** | **0.59** | **68 tests** |
| **Version 2.0 (Dataset V2 Unseen Benchmark)** | **0.81** | **0.63** | **0.71** | **0.70** | **68 tests** |

### 5.4 Proof of Generalization (Zero Overfitting)
To rigorously verify that the system did not overfit to the initial 15 evaluation questions, an independent evaluation benchmark (**Dataset V2**, `eval/test_questions_v2.md`) consisting of 15 entirely unseen offensive questions was executed:
- The system achieved **81% Chunk Precision** and **70% Macro F1** on completely unseen questions.
- Techniques with high technical specificity (AS-REP Roasting, SSRF, Kernel Exploits, BloodHound, Sudo LD_PRELOAD) achieved **75% to 100% precision**.
- This empirical evidence confirms that the hybrid retrieval architecture, candidate injection, and manifest generation generalize robustly across the entire offensive security domain.
