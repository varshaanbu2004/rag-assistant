import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
collection = chromadb.PersistentClient(path="chroma_db").get_collection("schemes")

question = "Who is excluded from PM-KISAN benefits?"
results = collection.query(query_embeddings=model.encode([question]).tolist(), n_results=3)

for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print(meta["source"], "page", meta["page"])
    print(doc[:300], "\n---")