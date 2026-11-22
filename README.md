# Rural Scheme Advisor

A RAG chatbot that answers farmers' questions about PM-KISAN and PMFBY from official documents only. Every answer cites file and page, and says "I could not find this in the documents I have." instead of guessing. Chat UI is Streamlit.

## How it works (retrieval pipeline)

1. **Vector search** — semantic search in ChromaDB with all-MiniLM-L6-v2 embeddings
2. **BM25 keyword union** — keyword search merged with vector results
3. **Neighbor expansion** — includes adjacent chunks to capture split lists (e.g., exclusion criteria)
4. **Query rewriting** — Gemini rewrites the farmer's question in formal document wording
5. **Combined retrieve** — searches with both original and rewritten questions, merges and deduplicates results

## Results (retrieval key-phrase coverage, not answer accuracy)

| Method | PM-KISAN | PMFBY (no-scheme test) | No-scheme |
|--------|----------|------------------------|-----------|
| Vector search (k=8) | 64% | — | — |
| + Keyword union | 89% | — | — |
| + Neighbor expansion | 91% | — | — |
| + Query rewriting | 95% | — | — |
| Combined (original + rewritten) | 100% (20 questions) | 70% (forced no-scheme) | — |

- PM-KISAN: 20 test questions, 100% combined coverage
- PMFBY: manual review only; forced no-scheme test scores 70%
- No-scheme: 9 questions never name a scheme, so auto-detect cannot route them

## Known limitations

- Documents are from 2020 (PM-KISAN) and 2023 (PMFBY); rules may be outdated
- No-scheme PMFBY retrieval is 70% in a forced no-scheme test
- 9 questions never name a scheme so auto-detect cannot route them
- PMFBY answers were checked by manual review only

## Run locally

```bash
pip install -r requirements.txt
python src/build_index.py
streamlit run app/streamlit_app.py
```

No secrets required. The app reads `GOOGLE_API_KEY` from the environment; set it before running if you want Gemini answers.

## Live demo

LIVE_LINK_HERE

## Architecture diagram

TODO