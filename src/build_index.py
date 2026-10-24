import shutil
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import load_chunks

shutil.rmtree("chroma_db", ignore_errors=True)   # start fresh each run

chunks = load_chunks()
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("schemes")

texts = [c["text"] for c in chunks]
embeddings = model.encode(texts, show_progress_bar=True).tolist()

collection.add(
    ids=[c["chunk_id"] for c in chunks],
    documents=texts,
    embeddings=embeddings,
    metadatas=[{"source": c["source"], "page": c["page"], "page_end": c["page_end"], "scheme": c["scheme"]} for c in chunks],
)
print("Stored:", collection.count())