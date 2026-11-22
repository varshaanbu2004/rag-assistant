import sys
from pathlib import Path
from pypdf import PdfReader

if len(sys.argv) < 2:
    print('Usage: python src/find_phrase.py "word or phrase"')
    sys.exit(1)

word = " ".join(sys.argv[1:]).lower()
hits = 0
for pdf in sorted(Path("data/raw").glob("pmfby_*.pdf")):
    for n, page in enumerate(PdfReader(pdf).pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        for part in text.split(". "):
            if word in part.lower() and hits < 15:
                hits += 1
                print(f"{pdf.name} p{n}: {part[:160]}")
print(hits, "hits shown (max 15)")