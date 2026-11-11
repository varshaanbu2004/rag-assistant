PROJECT BRIEFING 

ABOUT ME
- Final-year student, comfortable with Python, building this as a resume project and to learn practically.
- Windows laptop, 16 GB RAM, Python 3.13, VS Code, Git/GitHub. Everything must be free-tier.
- I am a beginner at building: please give task-wise steps with the reason for each and its expected impact, change one thing at a time, and keep replies short because my chat limit is small. Do not ask me to paste big chunk dumps or whole CSV files.

PROJECT: Rural Scheme Advisor (agriculture schemes, India)
A RAG chatbot that answers farmers' questions about government schemes in simple language, from official documents only. Every answer cites file and page, and says "I could not find this in the documents I have." instead of guessing. Chat UI is Streamlit. Repo is on GitHub (rag-assistant).

TECH STACK
- Python, ChromaDB (vector store), sentence-transformers all-MiniLM-L6-v2 (embeddings), rank-bm25 (keyword search), pypdf, Streamlit.
- LLM: Gemini free tier via google-genai. Model in use: gemini-3.5-flash-lite (fast, 1-5 s). The main model gemini-3.8-flash took 479 s for one answer and returned 503, so it is not usable.
- Free-tier limit: 15 requests/minute. Combined retrieval makes 2 Gemini calls per question (rewrite + answer), so I hit 429 errors on long runs.

DATA
- data/raw/ (not in Git): pmkisan_guidelines_rev2020.pdf, pmkisan_amendment_para8.pdf, pmkmy_faq.pdf (this is the PM Kisan Maan-Dhan pension FAQ, not PM-KISAN).
- PMFBY (crop insurance) documents: Downloaded and addded in the sorces_log.
- Documents are from 2020, so rules may be outdated.

HOW THE PIPELINE WORKS
1. ingest.py: reads PDFs, cleans text, makes ~800-character chunks with overlap, continuous across page breaks, keeps source, page, page_end, scheme.
2. build_index.py: embeds chunks into ChromaDB.
3. hybrid.py: vector search + BM25 keyword search (union), neighbor expansion (also takes the chunks before and after each hit, because the exclusion list was split across chunks), query rewriting, and combined_retrieve (original question + rewritten question merged). Scheme filter via a scheme field and a keyword-based detect_scheme().
4. rewrite.py: asks Gemini to rewrite the farmer's question in formal document wording; cached in evaluation/rewrite_cache.json.
5. ask.py: builds the prompt (use only the context, include every list item, cite [file, page], refuse if nothing relates), calls Gemini with retry on 503. ask(question, retriever=None) takes a retriever function.
6. app/streamlit_app.py: chat page.
7. evaluation/test_set.json (24 questions: original, rephrased, unseen-wording, 2 should-refuse), src/evaluate.py (retrieval key-phrase coverage, no Gemini calls), src/evaluate_answers.py (answer-level checks, writes evaluation/answers_review.csv).

PHASES
DONE: setup; data collection (PM-KISAN); basic RAG; Streamlit app + README + screenshots; advanced retrieval; PM-KISAN evaluation.
IN PROGRESS: PMFBY phase (multi-scheme retrieval and scheme routing).
LEFT: full 40-50 question evaluation + RAGAS; guardrails, logging, feedback buttons; deployment (FastAPI, Docker, Hugging Face Spaces) with a fallback model; polish (README architecture diagram, blog, demo video). Optional: Tamil support, reranker, agents.

RESULTS SO FAR (PM-KISAN, key-phrase retrieval coverage, NOT answer accuracy)
- Vector search k=8: 64% | + keyword union: 89% | + neighbor expansion: 91% | + query rewriting: 95% | combined original + rewritten: 100% (20 questions).
- Answer-level run: 17/17 automatic checks passed; 7 manual answers reviewed against the PDF and judged "a bit good" (not perfect). Both should-refuse questions (solar pump, KCC limit) correctly said "not found".
- Unseen-wording questions: appeal_v2 passed 100%; exclusions_v3 scored 88% (misses "institutional land").

KEY LESSONS AND BUGS FOUND
- Plain vector search failed on direct questions ("do income tax payers get benefits?") because the answer sat in a list chunk without its heading; BM25 fixed that.
- Neighbor expansion fixed the exclusion list split across 3 chunks.
- Rank fusion (RRF) buried a keyword hit at position 13, so I switched to a simple union.
- Rewriting fixed vocabulary mismatch ("cannot get" vs "excluded") but made state_uploads fail once; searching with both original and rewritten text fixed it.
- ask() once accepted a retriever argument but never used it, so answers silently came from plain vector search. Found by saving the exact prompt and checking page labels.
- A perfect retrieval score does not guarantee a correct answer, so retrieval and generation are evaluated separately.
- Rule I follow: fix the system, not the test; edit a test phrase only if the phrase itself is wrong.

CURRENT PROBLEM (needs help)
After changing hybrid.py to index all schemes (_chunks = load_chunks()) and adding PMFBY routing, PM-KISAN retrieval scores moved:
- state_uploads (neighbors and combined): 100% -> 0%
- exclusions (neighbors 8+4): 100% -> 50%
- vector k=8 exclusions: 62% -> 25%, even though vector search is filtered to PM-KISAN and those chunks should not have changed.
- Combined now sends ~38.5 chunks on average (was 27.4), so prompts are longer.
Likely causes I am checking with src/check_chunks.py: a stale ChromaDB index versus load_chunks() (rebuild with build_index.py), shifted chunk boundaries, or test questions missing the scheme field. 

NEXT STEPS PLANNED
1. Find and fix the PM-KISAN score drop (hold off on new questions until fixed).
2. Add ~12 PMFBY test questions with short must_contain phrases copied from the PDF, plus 3 cross-scheme and 2 should-refuse questions.
3. Add a leak check (PM-KISAN answers must cite only pmkisan_ files, PMFBY answers only pmfby_ files).
4. Add a scheme selector in the Streamlit sidebar.
5. Update notes.md and README, commit, tag v0.2-pmfby.

WHAT I WANT FROM YOU
Help me with the next step only, in task-wise form (task, reason, expected impact, exact commands or code), and tell me exactly which small output to paste back so I save chat limit.

## Log (the agent appends here after every task)
- [date] task, files changed, scores before and after, open problems
- [2026-11-11] Task A: `src/hybrid.py` `neighbor_retrieve` — tier-1 unchanged (top kv vector + kb keyword expanded with neighbors, scheme filter kept); added tier-2 vector ranks 9-20 (same filtered candidates) appended alone, no neighbors, deduped vs tier-1. `EXCLUDED_SOURCES={"pmkisan_faq.pdf"}` kept (see report). Scores (combined, `python src/evaluate.py` logic, no Gemini, cached rewrites): neighbors AVERAGE 93% / 26.3 chunks, combined AVERAGE 100% / 29.7 chunks; no questions <100% in combined (state_uploads, exclusions, exclusions_v3, appeal_v2 all 100%). Open: Task B pending (verify pmfby_ files, run build_index.py, report chunk counts) — not started.