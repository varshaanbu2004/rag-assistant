from ingest import load_chunks
from ask import embedder, collection

QUESTION = "Who is excluded from PM-KISAN benefits?"
KEYWORDS = ["constitutional", "local bodies", "institutional land", "income tax"]

# Which chunks contain the exclusion text?
chunks = load_chunks()
targets = {}
for c in chunks:
    if c["scheme"] != "PM-KISAN":
        continue
    found = [k for k in KEYWORDS if k in c["text"].lower()]
    if found:
        targets[c["chunk_id"]] = found
        print(c["chunk_id"], "pages", c["page"], "-", c["page_end"], "->", found)

# Where do those chunks rank for the question?
res = collection.query(
    query_embeddings=embedder.encode([QUESTION]).tolist(),
    n_results=40,
    where={"scheme": "PM-KISAN"},
)
print("\nRanks for the question:")
for rank, (cid, dist) in enumerate(zip(res["ids"][0], res["distances"][0]), start=1):
    if cid in targets:
        print("rank", rank, cid, f"distance {dist:.2f}", targets[cid])