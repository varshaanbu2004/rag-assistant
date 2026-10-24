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