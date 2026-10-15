import re
from pathlib import Path
from pypdf import PdfReader

CHUNK_SIZE = 800
OVERLAP = 150


def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)      # collapse repeated spaces
    text = re.sub(r"\n\s*\n+", "\n", text)   # remove blank lines
    return text.strip()


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):                   # avoid cutting mid-word
            space = text.rfind(" ", start, end)
            if space > start + size // 2:
                end = space
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_chunks(raw_dir="data/raw"):
    all_chunks = []
    for pdf_path in sorted(Path(raw_dir).glob("*.pdf")):
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages, start=1):
            text = clean_text(page.extract_text() or "")
            for i, chunk in enumerate(chunk_text(text)):
                all_chunks.append({
                    "chunk_id": f"{pdf_path.stem}_p{page_num}_c{i}",
                    "source": pdf_path.name,
                    "page": page_num,
                    "text": chunk,
                })
    return all_chunks


if __name__ == "__main__":
    chunks = load_chunks()
    print("Total chunks:", len(chunks))
    print(chunks[5])
    