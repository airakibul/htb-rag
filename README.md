# HTB Cheatsheet Assistant (RAG)

## Overview

RAG system answering offensive security questions from 513 HTB writeups.
All answers grounded in writeup text with machine citations — not generic AI output.

## Architecture

```
raw/*.md ──► chunker ──► embedder (Gemini) ──► ChromaDB
                    └──► graph_builder ──────► NetworkX graph

query ──► HybridRetriever
            ├── BM25 (lexical)
            ├── ChromaDB (Gemini semantic)
            └── NetworkX (graph traversal)
          └──► Synthesizer (Groq LLaMA 70B)
          └──► FastAPI /query response
```

## Tech Stack

| Component       | Tool                         | Purpose         |
|-----------------|------------------------------|-----------------|
| Embedding       | Gemini text-embedding-004    | Semantic search |
| Vision          | Gemini gemini-1.5-flash      | Image describe  |
| LLM             | Groq llama-3.3-70b-versatile | Answer synth    |
| Vector Store    | ChromaDB (local)             | Chunk storage   |
| Knowledge Graph | NetworkX (local)             | Cross-machine   |
| API             | FastAPI                      | Interface       |

## Setup

### 1. Get API Keys (both free)

- **Gemini**: [aistudio.google.com](https://aistudio.google.com) → Get API Key
- **Groq**: [console.groq.com](https://console.groq.com) → API Keys → Create

### 2. Windows Defender Exclusion (required for HTB files)

```powershell
Add-MpPreference -ExclusionPath "c:\Brain Station 23\htb-wiki\raw"
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure .env

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
RAW_DIR=c:\Brain Station 23\htb-wiki\raw
```

## Running

### Ingest (once, ~1 hour)

```bash
python -m src.ingest                    # full ingest
python -m src.ingest_missing            # incremental ingest for missing files
python -m src.ingest --file htb-box.md  # single file
python -m src.ingest --dry-run          # stats only
python -m src.ingest --skip-images      # faster (no vision)
```

### Start API

```bash
uvicorn src.api:app --reload --port 8000
```

### Query

```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"Windows privilege escalation cheatsheet\"}"
```

### API Endpoints

| Method | Path                  | Purpose                          |
|--------|-----------------------|----------------------------------|
| POST   | `/query`              | Full RAG → cited answer          |
| POST   | `/retrieve`           | Raw retrieval (debug / eval)     |
| GET    | `/health`             | Status + index stats             |
| GET    | `/machines`           | All machine names in graph       |
| GET    | `/techniques`         | All technique names in graph     |
| GET    | `/machine/{name}`     | Machine detail (tools, CVEs)     |

## Evaluation

1. Fill `eval/answer_key.md` manually (grep commands included in file).
2. Start the API server.
3. Run the evaluator:

```bash
python eval/evaluator.py                     # all 15 questions
python eval/evaluator.py --questions 1,6,7   # subset
```

Results are written to `eval/results.md` and `eval/answers_generated.md`.

## Design

See [design_note.md](design_note.md) for architectural decisions and trade-offs.
