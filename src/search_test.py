import chromadb
from sentence_transformers import SentenceTransformer

QUESTIONS = [
    "How much money does PM-KISAN give per year?",
    "Who is excluded from PM-KISAN benefits?",
    "Is Aadhaar compulsory?",
    "What is the cut-off date for eligibility?",
    "How do I apply for crop insurance?",  # not in the documents on purpose
]

model = SentenceTransformer("all-MiniLM-L6-v2")
collection = chromadb.PersistentClient(path="chroma_db").get_collection("schemes")

for q in QUESTIONS:
    results = collection.query(
    query_embeddings=model.encode([q]).tolist(),
    n_results=3,
    where={"scheme": "PM-KISAN"},
)
    print("\n" + "=" * 70)
    print("QUESTION:", q)
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        print(f"\n[{meta['source']} | page {meta['page']} | distance {dist:.2f}]")
        print(doc[:500])