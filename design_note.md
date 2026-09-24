# Design Notes — HTB Cheatsheet Assistant (RAG)

## 1. Chunking Strategy

Fixed-size chunking (e.g. 512 tokens) is standard for generic corpora but destructive for HTB writeups. Exploit sequences span multiple commands with interleaved output — splitting mid-step severs the relationship between a command and its result, making the chunk useless for cheatsheet generation. HTB writeups already encode attack-step boundaries through `##` (phase) and `###` (step) headings. We split on these natural boundaries instead.

Four file shapes are handled: **normal** files split at `###` with `####` sub-splits for oversized blocks; **flat/old** writeups lacking `###` fall back to `##`; **mega** files (>100 KB) are constrained by the 600-token limit per chunk; and **stub** writeups under 500 words are emitted as a single chunk flagged `stub_file=True`.

Every chunk is prefixed with a breadcrumb — `[htb-certified | Shell as Admin > Exploit ESC9]` — so the synthesizer can cite machines automatically without auxiliary tracking. Image markdown lines are stripped from text chunks, but informational screenshots are described by Gemini Vision and stored as separate `image_desc` chunks carrying identical metadata.

## 2. Retrieval Choice

Pure BM25 fails on broad queries. Asking for a "Windows privilege escalation cheatsheet" returns nothing useful because writeups say "abuse GenericAll" or "exploit ESC9" — they rarely contain the phrase "privilege escalation" verbatim. Pure embedding search fails in the opposite direction: exact identifiers like `CVE-2026-4480`, tool flags (`--alt-security-identities`), or usernames sit in a sparse region of embedding space with poor nearest-neighbour recall.

The hybrid approach addresses both failure modes. BM25 handles exact CVE, tool, and flag lookups. Gemini `text-embedding-004` vectors handle conceptual queries, using asymmetric task types (`RETRIEVAL_QUERY` vs `RETRIEVAL_DOCUMENT`) for better query-document alignment. The NetworkX knowledge graph surfaces cross-machine relationships — when the user asks about ADCS, the graph links techniques to every machine that demonstrated them, enabling citations like *(seen on: Certified, Absolute)*.

Reciprocal Rank Fusion merges the BM25 and vector lists without score normalisation, avoiding the brittleness of raw score combination. ChromaDB metadata filters (`os`, `difficulty`) prune the search space before retrieval.

Hallucination carries real cost in this domain — a fabricated machine name or wrong CVE in a penetration-test cheatsheet misleads an analyst mid-engagement. Low temperature (0.1) and a strict system prompt requiring per-technique citations keep the synthesizer grounded in retrieved evidence.

## 3. Next Improvement

The highest-impact upgrade is **cross-encoder re-ranking**. After BM25 + vector retrieval returns ~16 candidates, a cross-encoder such as `ms-marco-MiniLM-L-6-v2` rescores each (query, chunk) pair with full attention. This improves precision without affecting recall. In the security context precision matters more — a cheatsheet with 5 perfectly relevant entries is more actionable than 10 mixed results. The model is small enough to run on CPU with no API cost, adding <200 ms latency per query.
