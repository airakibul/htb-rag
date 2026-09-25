# HTB Cheatsheet Assistant (RAG)

An offensive security Retrieval-Augmented Generation (RAG) assistant built over the Hack The Box (HTB) writeup corpus. Answers natural-language questions about penetration testing techniques, privilege escalation paths, and Active Directory attacks with grounded, verifiable citations to specific HTB machines (e.g. `(seen on: Absolute, APT)`).

---

## Architecture Overview

```
raw/*.md ──► AST & Heading Chunker ──► Gemini Embedding ──► ChromaDB (Vector Store)
                                 └──► Knowledge Graph  ──► NetworkX (Graph Store)

User Query ──► HybridRetriever
                 ├── BM25 (Lexical matching for tools, CVEs, exact flags)
                 ├── ChromaDB (Dense semantic retrieval via Gemini embeddings)
                 └── NetworkX (Cross-machine attack graph traversal)
               └──► Reciprocal Rank Fusion (RRF)
               └──► Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2)
               └──► Source Diversification (anti-monopoly filtering)
               └──► Synthesizer (Groq openai/gpt-oss-120b with fallback chain)
               └──► FastAPI REST API (`/query`, `/retrieve`)
```

---

## Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **LLM Synthesis** | Groq `openai/gpt-oss-120b` *(fallback: 20b & Gemini Flash)* | Strict cited answer generation |
| **Embeddings** | Google Gemini `gemini-embedding-001` | Dense semantic chunk representation |
| **Vision (Optional)** | Google Gemini `gemini-2.5-flash` | Screenshot and diagram description |
| **Vector DB** | ChromaDB (local persistence in `./db/chroma`) | Chunk storage & semantic indexing |
| **Lexical Search** | BM25 (`rank-bm25`) | Exact keyword, tool, and CVE search |
| **Cross-Encoder** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Deep contextual query-chunk re-ranking |
| **Knowledge Graph** | NetworkX (`./graph/htb_graph.json`) | Machine–Technique–CVE relationship graph |
| **API Framework** | FastAPI + Uvicorn | High-performance async REST API |
| **Test Suite** | Pytest | Unit testing chunker, embedder, retriever |

---

## Prerequisites

- **Python 3.10 – 3.12** installed on your system.
- **Git** installed.
- **Free API Keys:**
  - **Google Gemini API Key:** [Google AI Studio](https://aistudio.google.com/) *(Free)*
  - **Groq API Key:** [Groq Console](https://console.groq.com/) *(Free)*

---

## Step-by-Step Setup Guide (A to Z)

### Step 1: Clone the Repository

Open your terminal or command prompt and clone the repository:

```bash
git clone https://github.com/airakibul/htb-rag.git
cd htb-rag
```

---

### Step 2: Create and Activate Virtual Environment

Create an isolated Python virtual environment to avoid package conflicts:

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks script execution, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

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

Install all required Python libraries via pip:

```bash
pip install -r requirements.txt
```

> **Note on Reranker Model:** On the first query or test, `sentence-transformers` will automatically download the lightweight cross-encoder model (`ms-marco-MiniLM-L-6-v2`, ~80 MB).

---

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   *(Or on Windows CMD: `copy .env.example .env`)*

2. Open `.env` in any text editor and fill in your API keys:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_key_here
   GROQ_API_KEY=gsk_...your_groq_key_here
   RAW_DIR=./raw
   ```

---

### Step 5: Windows Defender Exclusion (Important for Windows Users)

Because HTB writeups discuss real-world exploits, proof-of-concept scripts, and CVE payloads, Windows Defender might falsely flag sample walkthrough lines. Add an exclusion for the project raw folder:

```powershell
Add-MpPreference -ExclusionPath (Get-Location).Path
```

---

### Step 6: Download the Raw Corpus Dataset

To download the 462 official raw HTB walkthrough markdown files from [htb-wiki](https://github.com/0xh7ml/htb-wiki), run the included automated fetcher script:

```bash
python scripts/fetch_corpus.py
```

*This will download and extract all markdown files directly into the `./raw` directory.*

---

### Step 7: Ingest and Index the Dataset

Run ingestion to chunk the documents, generate embeddings via Gemini, populate ChromaDB, and build the NetworkX knowledge graph:

```bash
# Full ingestion (indexes all writeups, ~45-60 mins depending on API speed)
python -m src.ingest

# Faster ingestion (skips screenshot vision processing)
python -m src.ingest --skip-images

# Dry run (prints chunk statistics without calling embedding API)
python -m src.ingest --dry-run
```

> **Precomputed Graph:** The repository already includes the pre-built knowledge graph at [graph/htb_graph.json](graph/htb_graph.json), so graph traversal works immediately.

---

### Step 8: Start the API Server

Start the FastAPI application using Uvicorn:

```bash
uvicorn src.api:app --reload --port 8000
```

Once started, open your browser to view the interactive Swagger API documentation:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

### Step 9: Querying the System

You can test the API using `curl` or any API client (Postman, Bruno, etc.):

#### Example: Windows Privilege Escalation Cheatsheet (Reference Query)

**Using cURL:**
```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"Provide me the Windows privilege escalation cheatsheet.\"}"
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

Run the automated evaluation benchmark against the 15 hand-curated evaluation questions:

```bash
# Evaluate all 15 questions
python eval/evaluator.py

# Evaluate a specific subset of questions
python eval/evaluator.py --questions 1,6,7
```

- Evaluation scores and metrics are output to [eval/results.md](eval/results.md).
- Full LLM generated answers are written to [eval/answers_generated.md](eval/answers_generated.md).

---

### Step 11: Run Unit Tests

Execute the unit test suite to verify all core components:

```bash
pytest
```

---

## API Endpoints Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/query` | Full RAG pipeline: Hybrid retrieval + synthesis with citations. |
| `POST` | `/retrieve` | Raw retrieval debug endpoint (returns ranked chunks and graph hits). |
| `GET` | `/health` | Server status, indexed chunk count, and graph stats. |
| `GET` | `/machines` | List all machine names indexed in the knowledge graph. |
| `GET` | `/techniques`| List all offensive security techniques in the graph. |
| `GET` | `/machine/{name}`| Detail view of tools and CVEs associated with a machine. |

---

## Evaluation & Design Documentation

- **Evaluation Writeup:** Detailed precision/recall metrics, root-cause breakdown of corpus anomalies, and synthesis grounding analysis: [evaluation_writeup.md](evaluation_writeup.md).
- **Design Notes:** Chunking strategy, code-block fence preservation, semantic breadcrumb injection, and lexical vs. embedding trade-offs: [design_note.md](design_note.md).
- **Test Questions:** 15 curated evaluation questions: [eval/test_questions.md](eval/test_questions.md).
- **Hand-Derived Ground Truth:** Hand-verified answer key built by grepping raw files: [eval/answer_key.md](eval/answer_key.md).
