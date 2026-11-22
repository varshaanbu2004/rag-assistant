# Rural Scheme Advisor

A RAG chatbot that answers farmers' questions about PM-KISAN and PMFBY from official documents only. Every answer cites file and page, and says "I could not find this in the documents I have." instead of guessing. Chat UI is Streamlit.

## Tech stack

Python, ChromaDB, sentence-transformers all-MiniLM-L6-v2, rank-bm25, pypdf, Gemini free tier via google-genai, Streamlit.

## How it works (retrieval pipeline)

1. **Vector search** — semantic search in ChromaDB with all-MiniLM-L6-v2 embeddings
2. **BM25 keyword union** — keyword search merged with vector results
3. **Neighbor expansion** — includes adjacent chunks to capture split lists (e.g., exclusion criteria)
4. **Query rewriting** — Gemini rewrites the farmer's question in formal document wording
5. **Combined retrieve** — searches with both original and rewritten questions, merges and deduplicates results

## Results

| Step | PM-KISAN key-phrase coverage |
|------|------------------------------|
| Vector search (k=8) | 64 percent |
| + Keyword union | 89 percent |
| + Neighbor expansion | 91 percent |
| + Query rewriting | 95 percent |
| Combined (original + rewritten) | 100 percent (20 questions) |

| Test set (39 questions) | Combined retrieval |
|-------------------------|--------------------|
| Scheme given — PM-KISAN | 100 percent |
| Scheme given — PMFBY | 100 percent |
| Scheme given — avg chunks sent | 45.4 chunks |
| Scheme not given — PM-KISAN | 95.5 percent |
| Scheme not given — PMFBY | 70 percent |
| Scheme not given — avg chunks sent | 43.4 chunks |

Key-phrase coverage, not answer accuracy.

## Quality checks

- Leak check: 0 leaks
- PM-KISAN answer checks: 15 of 15 passed
- Refusal checks: passed for the solar pump and KCC limit questions
- PMFBY answers: checked by manual review against the PDF pages

## Known limitations

- Documents are from 2020 (PM-KISAN) and 2023 (PMFBY); rules may be outdated
- Questions that do not name a scheme use a per-scheme fallback search
- PMFBY with no scheme is weaker (70 percent in the forced test); users can pick the scheme in the sidebar
- PMFBY answers were checked by manual review only

## Run locally

```bash
pip install -r requirements.txt
python src/build_index.py
streamlit run app/streamlit_app.py
```

A Gemini key is required. Set it as `GOOGLE_API_KEY` in the environment or in a local `.env` file. The 4 PDFs must be in `data/raw/`.

## Live demo

LIVE_LINK_HERE

## Architecture diagram

TODO