from pathlib import Path
from pypdf import PdfReader

for pdf_path in sorted(Path("data/raw").glob("*.pdf")):
    reader = PdfReader(pdf_path)
    total_chars = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        total_chars += len(text)

    print(f"\n=== {pdf_path.name} ===")
    print("Pages:", len(reader.pages))
    print("Total characters:", total_chars)
    first_text = reader.pages[0].extract_text() or ""
    print(first_text[:300])