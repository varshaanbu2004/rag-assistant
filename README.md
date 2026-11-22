# Rural Scheme Advisor

A RAG chatbot that answers farmers' questions about PM-KISAN and PMFBY from official documents only. Every answer cites file and page, and says "I could not find this in the documents I have." instead of guessing. Chat UI is Streamlit.

## Tech stack

Python, ChromaDB, sentence-transformers all-MiniLM-L6-v2, rank-bm25, pypdf, Gemini free tier via google-genai, Streamlit.

## How it works (retrieval pipeline)

1. Vector search: semantic search in ChromaDB with all-MiniLM-L6-v2 embeddings
2. BM25 keyword union: keyword search merged with vector results
3. Neighbor expansion: includes adjacent chunks to capture split lists (for example exclusion criteria)
4. Query rewriting: Gemini rewrites the farmer's question in formal document wording
5. Combined retrieve: searches with both original and rewritten questions, merges and deduplicates results

## Results

All scores are key-phrase retrieval coverage (does the needed phrase appear in the chunks sent to Gemini), not answer accuracy.

Retrieval ladder on the original 20 PM-KISAN questions:

| Step | Coverage |
|------|----------|
| Vector search (k=8) | 64 percent |
| + Keyword union | 89 percent |
| + Neighbor expansion | 91 percent |
| + Query rewriting | 95 percent |
| Combined (original + rewritten) | 100 percent |

Current test set (39 questions), combined retrieval:

| Setting | PM-KISAN | PMFBY | Avg chunks sent |
|---------|----------|-------|-----------------|
| Scheme given | 100 percent | 100 percent | 45.4 |
| Scheme not given (forced test) | 95.5 percent | 70 percent | 43.4 |

## Quality checks

- Leak check: 0 leaks
- PM-KISAN answer checks: 15 of 15 passed
- Refusal checks: passed for the solar pump and KCC limit questions
- PMFBY answers: checked by manual review against the PDF pages

## Known limitations

- Documents are from 2020 (PM-KISAN) and 2023 (PMFBY); rules may be outdated, so answers carry a "verify on the official portal" note
- Questions that do not name a scheme use a per-scheme fallback search; PMFBY with no scheme is weaker (70 percent in the forced test), and users can pick the scheme in the sidebar
- PMFBY answers were checked by manual review only

## Run locally

```bash
pip install -r requirements.txt
python src/build_index.py
streamlit run app/streamlit_app.py
```

A Gemini key is required. Set it as GOOGLE_API_KEY in the environment or in a local .env file. The 4 PDFs must be in data/raw/.

## Live demo

LIVE_LINK_HERE

## Architecture diagram

TODO