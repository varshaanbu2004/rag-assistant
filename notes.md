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