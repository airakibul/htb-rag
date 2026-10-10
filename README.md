# HTB Cheatsheet Assistant (RAG) — Version 2.0

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-orange.svg)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/Tests-68%20Passed-brightgreen.svg)](https://pytest.org)
[![Latency](https://img.shields.io/badge/P90%20Latency-~1.95s%20(CPU)-success.svg)]()
[![Precision](https://img.shields.io/badge/V2%20Precision-81%25-blueviolet.svg)]()

An offensive security Retrieval-Augmented Generation (RAG) assistant built over 462 Hack The Box (HTB) writeups. Answers natural-language questions regarding penetration testing tactics, privilege escalation paths, Active Directory abuse, and CVE exploitation with grounded, verifiable citations to specific HTB machines (e.g. `(seen on: Absolute, APT)`).

> 📘 **Looking for the Upgrade Changelog?** See [version-2.md](version-2.md) for a comprehensive breakdown of architectural refactoring, performance benchmarks, and empirical evaluations between Version 1.0 (`main`) and Version 2.0 (`2nd_week`).

---

## Key Performance Indicators (Version 2.0)

| Metric / KPI | Version 1.0 Baseline | Version 2.0 (V1 Calibrated) | Version 2.0 (V2 Unseen Benchmark) | Status |
|:---|:---:|:---:|:---:|:---:|
| **Chunk Precision** | 0.25 (25%) | **0.66 (66%)** | **0.81 (81%)** | **High Precision** 🎯 |
| **Chunk Recall** | 0.08 (8%) | **0.59 (59%)** | **0.63 (63%)** | **+687% relative** 🚀 |
| **Corpus Graph Recall** | 0.12 (12%) | **0.83 (83%)** | **0.71 (71%)** | **Broad Coverage** 🌐 |
| **Macro F1 Score** | 0.11 (11%) | **0.59 (59%)** | **0.70 (70%)** | **Balanced Excellence** ✅ |
| **P90 Retrieval Latency** | ~8.50s (CPU) | **~1.95s (CPU)** | **~2.05s (CPU)** | **76% Latency Reduction** ⚡ |
| **Unit Test Suite** | 22 tests | **68 passed tests** | **68 passed tests** | **100% Passing** |

---

## Architecture Overview

```
raw/*.md ──► AST & Heading Chunker ──► SentenceTransformer Embedding ──► ChromaDB (Vector Store)
                                 └──► Knowledge Graph Builder     ──► NetworkX (Graph Store)

User Query ──► QueryEnhancer (Scope & Intent Detection)
                 ├── Specific Queries ──► Injects KG Candidate Entities (Technique/CVE)
                 └── Broad Queries    ──► Injects Comprehensive Machine Manifest Table
             ──► Multi-Stage HybridRetriever
                 ├── BM25 (Lexical matching for tools, CVEs, syntax)
                 ├── ChromaDB (Semantic dense vector search)
                 └── NetworkX (Relational graph traversal)
             ──► Reciprocal Rank Fusion (RRF, k=60)
             ──► Cross-Encoder Neural Reranking (ms-marco-MiniLM-L-6-v2, top-12 pool)
             ──► Source Diversification (Per-machine quota enforcement)
             ──► Dual-Layer Synthesizer (top-k procedural chunks + manifest table ──► LLM)
             ──► FastAPI REST API (`/query`, `/retrieve`, `/machines`, etc.)
```

### Layered Modular Layout (Hexagonal / Clean Architecture)

```
src/
├── domain/            # Core business models & abstract interfaces (Zero I/O dependencies)
│   ├── interfaces.py  # Abstract contracts (VectorStore, GraphStore, LLMProvider, ChunkingStrategy, etc.)
│   ├── models.py      # Pure data transfer objects (Chunk, RetrievalResult, EnhancedQuery, SynthesisResult)
│   └── value_objects.py # Value objects and validation rules
├── infrastructure/    # Concrete adapters for external systems, DBs, models, and LLMs
│   ├── chroma_store.py          # VectorStore adapter (ChromaDB + in-memory fallback)
│   ├── networkx_graph.py        # GraphStore adapter (NetworkX + JSON serialization)
│   ├── sentence_transformer.py  # EmbeddingService adapter (all-MiniLM-L6-v2)
│   ├── cross_encoder.py         # Neural Reranker adapter (ms-marco-MiniLM-L-6-v2)
│   ├── groq_provider.py         # LLMProvider adapter (Groq Qwen 2.5 / Llama 3)
│   └── gemini_provider.py       # LLMProvider adapter (Google Gemini 2.5/3.8)
├── pipeline/          # Orchestration pipeline (depends strictly on domain interfaces)
│   ├── chunker.py         # Strategy-pattern markdown chunker + breadcrumb context injection
│   ├── query_enhancer.py  # Query intent detection, OS scoping, and entity expansion
│   ├── retriever.py       # Multi-stage hybrid retriever + latency-tuned neural reranker
│   └── synthesizer.py     # Dual-layer synthesizer with prompt citations
├── graph/             # Knowledge graph domain logic & manifest extraction
│   ├── builder.py     # Graph construction from writeup corpus
│   ├── querier.py     # Relational graph topology and node queries
│   └── manifest.py    # Graph-assisted machine manifest generation with OS filtering
└── api/               # Presentation layer (HTTP REST endpoints)
    ├── server.py      # FastAPI application initialization & CORS middleware
    ├── routes.py      # REST endpoint routes (/query, /retrieve, /machines, /health)
    └── schemas.py     # Pydantic request and response schemas
```

---

## SOLID Architecture Design Principles

1. **Single Responsibility Principle (SRP):**
   - Each module handles a single, well-defined responsibility: `src.graph.manifest` generates machine manifests, `src.pipeline.query_enhancer` classifies query intent and target OS, and `src.infrastructure.cross_encoder` performs neural reranking.
2. **Open/Closed Principle (OCP):**
   - Open for extension, closed for modification. New vector stores (e.g., Qdrant, Milvus), graph engines (e.g., Neo4j), or LLMs (e.g., Anthropic, Ollama) can be plugged in by implementing domain interfaces without altering pipeline orchestration.
3. **Liskov Substitution Principle (LSP):**
   - Concrete implementations substitute domain abstractions seamlessly. `GroqProvider` and `GeminiProvider` both adhere strictly to `LLMProvider`, allowing transparent multi-provider fallback without caller side-effects.
4. **Interface Segregation Principle (ISP):**
   - Contracts in [`src/domain/interfaces.py`](src/domain/interfaces.py) are fine-grained and purpose-specific: `VectorStore`, `GraphStore`, `EmbeddingService`, `LLMProvider`, `Reranker`, and `ChunkingStrategy`.
5. **Dependency Inversion Principle (DIP):**
   - High-level orchestration layers (`HybridRetriever`, `Synthesizer`, `routes.py`) depend strictly upon abstract interfaces defined in the domain layer, not on concrete database drivers or vendor SDKs. Dependencies are injected via constructors.

---

## Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **LLM Synthesis** | Groq `qwen/qwen3.8-27b` *(fallback: Gemini Flash & OpenRouter)* | Low-latency, strict cited answer generation |
| **Embeddings** | SentenceTransformer `all-MiniLM-L6-v2` | Local 384-dim dense chunk embeddings |
| **Vector DB** | ChromaDB (local persistence in `./db/chroma`) | Persistent vector storage & semantic indexing |
| **Lexical Search** | BM25 (`rank-bm25`) | Exact keyword, tool name, and CVE matching |
| **Cross-Encoder** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Contextual query-chunk reranking (tuned 12-candidate pool) |
| **Knowledge Graph** | NetworkX (`./graph/htb_graph.json`) | Machine–Technique–CVE relationship graph & manifest injection |
| **API Framework** | FastAPI + Uvicorn | High-performance asynchronous REST API |
| **Test Suite** | Pytest | Comprehensive unit test suite (68 tests passing) |

---

## Prerequisites

- **Python 3.10 – 3.12** installed on your system.
- **Git** installed.
- **API Keys (Free):**
  - **Google Gemini API Key:** [Google AI Studio](https://aistudio.google.com/) *(Free)*
  - **Groq API Key:** [Groq Console](https://console.groq.com/) *(Free)*

---

## Step-by-Step Setup Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/airakibul/htb-rag.git
cd htb-rag
git checkout 2nd_week
```

---

### Step 2: Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks execution, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

**On Windows (Command Prompt - CMD):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Install Required Dependencies

```bash
pip install -r requirements.txt
```

> **Note on Reranker Model:** On the first query or test, `sentence-transformers` automatically downloads the lightweight cross-encoder model (`ms-marco-MiniLM-L-6-v2`, ~80 MB).

---

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   *(Or on Windows CMD: `copy .env.example .env`)*

2. Open `.env` and configure your API keys:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_key_here
   GROQ_API_KEY=gsk_...your_groq_key_here
   RAW_DIR=./raw
   ```

---

### Step 5: Windows Defender Exclusion (Recommended for Windows)

Because penetration testing writeups discuss real exploits, PoC scripts, and payloads, Windows Defender might flag walkthrough snippets in `raw/`. Add an exclusion for the repository folder:

```powershell
Add-MpPreference -ExclusionPath (Get-Location).Path
```

---

### Step 6: Download the Raw Corpus Dataset

To download the 462 official raw HTB walkthrough markdown files from [htb-wiki](https://github.com/0xh7ml/htb-wiki):

```bash
python scripts/fetch_corpus.py
```

*This downloads and extracts all markdown files directly into `./raw`.*

---

### Step 7: Ingest and Index the Dataset

```bash
# Full ingestion (indexes all writeups)
python -m src.ingest

# Fast ingestion (skips screenshot vision processing)
python -m src.ingest --skip-images

# Dry run (prints chunk statistics without calling embedding API)
python -m src.ingest --dry-run
```

> **Precomputed Graph:** The repository includes a precomputed knowledge graph at [graph/htb_graph.json](graph/htb_graph.json), so graph traversal and manifest injection work immediately out-of-the-box.

---

### Step 8: Start the API Server

```bash
uvicorn src.api:app --reload --port 8000
```

Once started:
- 🖥️ **Interactive Web Dashboard:** 👉 **[http://localhost:8000](http://localhost:8000)**
- 📖 **Interactive Swagger API Docs:** 👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

### Step 9: Querying the System

#### Example: Windows Privilege Escalation Cheatsheet

**Using cURL:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Provide me the Windows privilege escalation cheatsheet."}'
```

**Using PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/query" -Method Post `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body (ConvertTo-Json @{ question = "Provide me the Windows privilege escalation cheatsheet." })
```

**Using Python:**
```python
import requests

resp = requests.post(
    "http://localhost:8000/query",
    json={"question": "What is MS17-010 EternalBlue and which HTB machines demonstrate it?"}
)
print(resp.json()["answer"])
```

---

### Step 10: Run the Evaluation Benchmark

The evaluation system features a **Dual-Track Evaluation Methodology**:
- **Chunk Precision & Recall:** Measures the technical accuracy of top-k (5–8) retrieved chunks delivered into the LLM context.
- **Graph Corpus Recall:** Measures the catalog coverage of the Knowledge Graph Manifest table for broad cheatsheets.

```bash
# 1. Run canonical benchmark on Dataset V1 (15 questions)
python eval/evaluator.py

# 2. Run generalization benchmark on Dataset V2 (15 unseen questions)
python eval/evaluator.py --dataset v2

# 3. Evaluate against raw uncurated grep baselines
python eval/evaluator.py --raw-key
python eval/evaluator.py --dataset v2 --raw-key

# 4. Evaluate specific question subsets (e.g., questions 1, 6, 7)
python eval/evaluator.py --questions 1,6,7
```

- Benchmark reports are written to [eval/results.md](eval/results.md) and [eval/results_v2.md](eval/results_v2.md).
- Full LLM generated answers are saved to [eval/answers_generated.md](eval/answers_generated.md) and [eval/answers_generated_v2.md](eval/answers_generated_v2.md).

---

### Step 11: Run Unit Tests

Execute the test suite to verify all SOLID components, adapters, chunkers, and retrievers:

```bash
pytest -v
```

Expected output:
```text
============================== 68 passed in 1.45s ==============================
```

---

## API Endpoints Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/query` | Full RAG pipeline: Hybrid retrieval + neural reranking + dual-layer synthesis with citations. |
| `POST` | `/retrieve` | Raw retrieval debug endpoint (returns ranked chunks and graph candidate hits). |
| `GET` | `/health` | Server status, indexed chunk count, and knowledge graph node/edge counts. |
| `GET` | `/machines` | List all machine names indexed in the knowledge graph. |
| `GET` | `/techniques`| List all offensive security techniques indexed in the graph. |
| `GET` | `/machine/{name}`| Detail view of tools, categories, and CVEs associated with a specific machine. |

---

## Documentation Index

- 📄 **[version-2.md](version-2.md):** Complete Version 1.0 vs Version 2.0 Upgrade Manifest and Architecture Guide.
- 📐 **[design_note.md](design_note.md):** Deep architectural design notes, chunking strategies, hybrid RRF formulation, and sub-2s latency tuning.
- 📊 **[evaluation_writeup.md](evaluation_writeup.md):** In-depth empirical evaluation report, dual-track methodology, V1 and V2 benchmark analysis, and error taxonomy.
- 🗝️ **[test_set_answer_key.md](test_set_answer_key.md):** Corpus-wide hand-derived technical reference catalog across all 462 writeups.
- 🧪 **[eval/test_questions.md](eval/test_questions.md) & [eval/test_questions_v2.md](eval/test_questions_v2.md):** Official 15-question benchmark datasets (V1 and V2).
- 🎯 **[eval/answer_key.md](eval/answer_key.md) & [eval/answer_key_v2.md](eval/answer_key_v2.md):** Calibrated canonical ground truth answer keys.
- 📈 **[eval/results.md](eval/results.md) & [eval/results_v2.md](eval/results_v2.md):** Full automated evaluation output reports.
