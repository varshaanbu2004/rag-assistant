import re
from pathlib import Path
from pypdf import PdfReader

CHUNK_SIZE = 800
OVERLAP = 150
SCHEME_BY_PREFIX = {
    "pmkisan_": "PM-KISAN",
    "pmkmy_": "PM Kisan Maan-Dhan",
}


def scheme_for(filename):
    for prefix, scheme in SCHEME_BY_PREFIX.items():
        if filename.startswith(prefix):
            return scheme
    return "unknown"

def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)      # collapse repeated spaces
    text = re.sub(r"\n\s*\n+", "\n", text)   # remove blank lines
    return text.strip()


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = max(text.rfind(" ", start, end), text.rfind("\n", start, end))
            if cut > start + size // 2:
                end = cut
        chunks.append((start, text[start:end].strip()))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def page_at(offset, page_starts):
    page = page_starts[0][1]
    for start, num in page_starts:
        if start <= offset:
            page = num
        else:
            break
    return page


def load_chunks(raw_dir="data/raw"):
    all_chunks = []
    for pdf_path in sorted(Path(raw_dir).glob("*.pdf")):
        reader = PdfReader(pdf_path)
        full_text = ""
        page_starts = []
        for page_num, page in enumerate(reader.pages, start=1):
            page_starts.append((len(full_text), page_num))
            full_text += clean_text(page.extract_text() or "") + "\n"

        for i, (start, chunk) in enumerate(chunk_text(full_text)):
            all_chunks.append({
                "chunk_id": f"{pdf_path.stem}_c{i}",
                "source": pdf_path.name,
                "scheme": scheme_for(pdf_path.name),
                "page": page_at(start, page_starts),
                "page_end": page_at(start + len(chunk) - 1, page_starts),
                "text": chunk,
            })
    return all_chunks

if __name__ == "__main__":
    chunks = load_chunks()
    print("Total chunks:", len(chunks))
    print(chunks[5])
    