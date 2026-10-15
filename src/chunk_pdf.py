from pathlib import Path
from pypdf import PdfReader

CHUNK_SIZE = 800   # characters per chunk
OVERLAP = 150      # characters shared between neighbouring chunks


def load_pages(pdf_path):
    reader = PdfReader(pdf_path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


all_chunks = []
for pdf_path in sorted(Path("data/raw").glob("*.pdf")):
    for page_num, text in load_pages(pdf_path):
        for i, chunk in enumerate(chunk_text(text, CHUNK_SIZE, OVERLAP)):
            all_chunks.append({
                "chunk_id": f"{pdf_path.stem}_p{page_num}_c{i}",
                "source": pdf_path.name,
                "page": page_num,
                "text": chunk,
            })

print("Total chunks:", len(all_chunks))
print("\nSample chunk:")
print(all_chunks[5])