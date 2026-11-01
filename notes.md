# Project Notes

## Day 1: Setup

- Installed Python 3.13, VS Code, Git; created venv and GitHub repo
- Stored the Gemini API key in .env and added .env to .gitignore

### Problems and fixes
- PowerShell blocked venv activation (execution policy) -> switched terminal to Command Prompt
- "pip is not recognized" -> venv was not active; activate it in every new terminal
- Connection reset error during the big install -> used --default-timeout, --retries and installed packages in smaller groups
- Gemini 404 (model retired) -> updated the model name
- Gemini 503 (server busy) -> retried a few minutes later
- Two git commands pasted together caused an error -> run commands one at a time

## Day 2: Data collection, chunking, indexing, retrieval

### What I built
- Downloaded 3 official PDFs into data/raw/: PM-KISAN revised operational guidelines (2020), amendment to para 8.1, and the PM Kisan Maan-Dhan FAQ
- src/ingest.py: reads PDFs, cleans text, splits into ~800-character chunks with 150 overlap, keeps source file and page number
- src/build_index.py: embeds chunks with all-MiniLM-L6-v2 and stores them in ChromaDB (121 chunks)
- src/search_test.py: runs 5 test questions and prints the top 3 chunks

### Problems and fixes
- Files were named .pdf.pdf because Windows hides extensions -> renamed in the terminal
- The "FAQ" I downloaded was for PM Kisan Maan-Dhan, not PM-KISAN -> renamed to pmkmy_faq.pdf
- Chunks ended mid-word -> chunk_text now cuts at a space
- Extra blank lines wasted space -> added clean_text()
- Chunks from the wrong scheme appeared in results -> added a "scheme" metadata field and a filter

### Retrieval test: before vs after scheme filter
Direct-answer chunk in top 3?

| Question | Before filter | After filter |
|---|---|---|
| Money per year | Yes (page 2, to verify) | Yes |
| Who is excluded | Yes (page 3) | Yes |
| Is Aadhaar compulsory | Yes | Yes |
| Cut-off date | Partly (page 3 dates, but not para 5.2) | Yes (para 5.2 at rank 3) |
| Crop insurance (not in data) | Returned unrelated chunks | Returned unrelated chunks |

Wrong-scheme chunks in results: 5 before the filter, 0 after.

### What I learned
- Semantic search sometimes ranks the exact phrase ("cut-off date") low, so keyword search (BM25) should help -> hybrid search later
- A distance cutoff cannot detect "not found": the irrelevant results (1.22 to 1.27) scored closer than the correct cut-off answer (1.38 to 1.42). The LLM prompt must handle "not found".
- The 2019 amendment and the 2020 guidelines both talk about Aadhaar, so the newest document should be preferred -> add a doc_date field later
- Lists that run across a page break get split (the exclusion list starts mid-list on page 3)
- The documents are from 2020, so newer rules may be missing

### Next
- Connect Gemini (src/ask.py) to produce cited answers
- Check whether the model says "not found" for questions outside the documents

## Day 3: Gemini answers, testing, and the exclusion-list problem

### What I built
- src/ask.py: retrieves chunks (filtered to PM-KISAN), sends them to Gemini with a strict prompt, and prints an answer with sources
- Prompt rule: answer only from the context, otherwise reply "I could not find this in the documents I have"
- Retry on 503 errors (waits 5 seconds, up to 3 tries)
- Changed chunking to run across page boundaries (page and page_end saved for each chunk)
- Added debug scripts: debug_retrieval.py and debug_rank.py

### First test (per-page chunks, k=4)
| Question | Correct? | Complete? | Citations right? |
|---|---|---|---|
| Money per year | Yes | Yes | Yes (pages 2 and 10, checked in the PDF) |
| Exclusions | Yes | No (4 of 8 items, 1 partial, 3 missing) | Yes |
| Cut-off date | Yes | Yes | Yes (page 3, para 5.2) |
| Crop insurance (not in data) | Correctly said "not found" | n/a | n/a |

Checked every answer against the PDF by hand. The "extra" land-transferee point in the exclusion answer is a real rule (page 5, para 5.3), not an invented one.

### Problem: exclusion list incomplete
- The PDF has 8 exclusion items on pages 2 and 3. The answer missed the first items (institutional landholders, constitutional posts, ministers and MPs)
- Cause: the list is cut by the page break, so retrieval got only the second half
- Fix tried: chunk across page boundaries
- Result: worse. With k=4 the system refused ("not found") for the exclusion question

### Debugging with data
- Checked what Gemini actually received: none of the 4 chunks mentioned exclusions, so the refusal was correct for the context it was given
- debug_rank.py showed the list was split into 3 chunks, and their ranks for the question were 6, 7 and 29
- The middle chunk (ranked 29) lists job titles but lacks the word "exclusion", because that heading was in another chunk
- Lesson: re-chunking can break questions that worked before, so rerun all test questions after every change

### Fix tried: k=8 (retrieve 8 chunks instead of 4)
| Setup | Exclusion items found (of 8) |
|---|---|
| Per-page chunks, k=4 | 4 full + 1 partial |
| Cross-page chunks, k=4 | 0 (refused) |
| Cross-page chunks, k=8 | 4 full + 2 partial, 2 missing |

- Still missing: pensioners and income tax payers
- Money, cut-off and crop-insurance answers stayed correct, and crop insurance still said "not found"
- Gemini added its own heading ("Families of Higher Economic Status") that is not in the PDF

### What I learned
- An answer can be correct on every line and still be incomplete, so evaluation must check completeness
- A distance cutoff cannot detect "not found", so the prompt rule handles it
- Checking answers against the source PDF caught problems that a quick read would miss
- The first run is slow because of library startup, so a Streamlit app (loads once) will feel faster

### Known problem (to fix in Week 2)
- The exclusion list is spread over 3 chunks and retrieval only finds part of it
- Planned fixes: hybrid search, reranker, structure-aware chunking
- The documents are from 2020, so newer rules should be checked on pmkisan.gov.in

### Next
- Streamlit chat page
- Add more schemes (PMFBY, KCC) so crop-insurance questions can be answered
- Week 2: hybrid search, reranker, evaluation set

### Speed fix
- Before: Gemini call took 98 to 178s per answer (retrieval only 0.2s)
- Changed: (write what you changed: lighter model name and/or thinking level)
- After: about 10 to 15s per answer
- Money, cut-off and crop-insurance answers stayed correct
- Exclusion answer unchanged: still missing some items (retrieval problem, Week 2)

### A Debugging Story
A parameter that is accepted but never used raises no error. I found it by saving the exact prompt and checking the page labels, so log what is sent to the model.

## Day 4: Retrieval fixes

- Baseline vector search (k=8): 60% key-phrase coverage on 6 test questions
- Keyword search (BM25) fixed direct questions; neighbor expansion fixed the exclusion list split across chunks
- Best setup (neighbors + keyword): 100% coverage, but longer prompts
- Bug: ask() accepted a retriever argument but never used it, so answers still came from plain vector search. Found it by saving the prompt (last_prompt.txt) and checking page labels
- After the fix: exclusion and income-tax answers are correct; crop insurance still says "not found"
- Wasted time on model switching: gemini-3.8-flash took 479s and hit 503; staying on gemini-3.5-flash-lite (2 to 6s)
- Lesson: evaluate retrieval and generation separately, and log what is sent to the model
- Metric is key-phrase retrieval coverage, not answer accuracy

## Day 6 to 8: Query rewriting, answer evaluation, rate limits

### Retrieval comparison (20 scored questions, key-phrase coverage)
| Method | Average | Chunks sent |
|---|---|---|
| Vector search, k=8 | 64% | 8 |
| Union (vector 8 + keyword 4) | 89% | 12 |
| Neighbors (vector 8 + keyword 4, radius 1) | 91% | 22.4 |
| Neighbors + query rewriting | 95% | 23.6 |
| Combined (original + rewritten question) | 100% | 27.4 |

- Keyword search fixed the direct questions (taxpayers, pensioners). Neighbor expansion fixed the exclusion list that was split across chunks.
- Two questions failed in every method until rewriting: "Which farmers cannot get PM-KISAN money?" and "If my name is missing, can I appeal?". Cause: the farmer's words do not match the document's words (the guideline says "excluded" and "not eligible").
- Query rewriting fixed both, but made `state_uploads` fail. The rewrite drifted away from the question ("Beneficiary data upload verification mandatory parameters PM-KISAN"). Searching with both the original and the rewritten question fixed it.
- Rank fusion (my first hybrid attempt) buried a keyword hit at position 13, found with a debug script. I switched to a simple union.

### Test set and answer evaluation
- Grew the test set from 6 to 24 questions: original wording, rephrased versions, two unseen-wording questions (exclusions_v3, appeal_v2), and two should-refuse questions (solar pump, KCC limit).
- evaluation/evaluate.py scores retrieval; evaluation/evaluate_answers.py checks the final Gemini answers.
- Automatic answer checks: 17/17 passed. 7 questions need manual review.
- Manual review against the PDF: it doesn't fully given the correct statement but it matched with the right answer.
- Refusal questions: solar pump and KCC limit both returned "I could not find this in the documents I have."

### Problems and fixes
- Every answer in the CSV said "ERROR: name 'question' is not defined". The script was using a variable that did not exist in its loop, and marked errors as FAIL. Fix: count errors separately and use t["question"].
- 429 RESOURCE_EXHAUSTED: the free tier allows 15 requests per minute, and each question makes two Gemini calls (rewrite and answer). Fixes: wait 12 seconds between questions, wait 60 seconds on a retry, and cache rewrites in evaluation/rewrite_cache.json.
- The main model (gemini-3.8-flash) took 479 seconds for one answer and then returned 503. Staying on gemini-3.5-flash-lite (1 to 5 seconds per answer).
- With the combined retriever, a question sends 20 to 33 chunks. Streamlit answers take about 10 to 12 seconds.
- Deleted one-off scripts (search_test, try_questions, try_rewrite, debug_app, debug_ask, debug_retrieval, test_neighbor).

### What I learned
- A perfect retrieval score does not guarantee a correct answer, so retrieval and generation must be evaluated separately.
- A parameter that is accepted but never used raises no error. Logging what is sent to the model found it.
- Rephrased questions exposed a weakness that the original wording hid.
- Fix the system, not the test: only edit a test phrase if the phrase itself is wrong.
- The score is key-phrase retrieval coverage on a small test set, not answer accuracy.

### Known limitations
- The guidelines are from 2020, so newer rules may be missing (check pmkisan.gov.in).
- No conversation memory: follow-up questions are treated as new questions.
- Free-tier rate limits (15 requests per minute) restrict heavy use.
- The exclusion list can still be incomplete when Gemini skips items, so the answer ends with a "verify on the official portal" note.

### Next
- Add PMFBY (crop insurance) with scheme routing
- Build a 40 to 50 question evaluation set and run RAGAS
- Logging, feedback buttons, deployment