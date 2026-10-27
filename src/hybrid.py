import re
from rank_bm25 import BM25Okapi
from ask import embedder, collection
from ingest import load_chunks

STOP = {"the", "a", "an", "is", "are", "of", "to", "for", "do", "does", "what",
        "who", "how", "in", "on", "and", "or", "get", "can", "i", "be", "by", "from"}


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


# Keyword index built in memory from the same chunks as the vector index
_chunks = [c for c in load_chunks() if c["scheme"] == "PM-KISAN"]
_by_id = {c["chunk_id"]: c for c in _chunks}
_bm25 = BM25Okapi([tokens(c["text"]) for c in _chunks])


def _meta(c):
    return {"source": c["source"], "page": c["page"],
            "page_end": c["page_end"], "scheme": c["scheme"]}


def _pack(ids):
    return [(_by_id[i]["text"], _meta(_by_id[i])) for i in ids]


def keyword_ids(question, n=20):
    scores = _bm25.get_scores(tokens(question))
    order = sorted(range(len(_chunks)), key=lambda i: scores[i], reverse=True)
    return [_chunks[i]["chunk_id"] for i in order[:n] if scores[i] > 0]


def vector_ids(question, n=20):
    res = collection.query(
        query_embeddings=embedder.encode([question]).tolist(),
        n_results=n,
        where={"scheme": "PM-KISAN"},
    )
    return res["ids"][0]


def keyword_retrieve(question, k=8):
    return _pack(keyword_ids(question, k))


def hybrid_retrieve(question, k=8, n=20):
    fused = {}
    for ids in (vector_ids(question, n), keyword_ids(question, n)):
        for rank, cid in enumerate(ids, start=1):
            fused[cid] = fused.get(cid, 0) + 1 / (60 + rank)
    top = sorted(fused, key=fused.get, reverse=True)[:k]
    return _pack(top)

def explain(question, phrase, k=8, n=20):
    v, b = vector_ids(question, n), keyword_ids(question, n)
    fused = {}
    for ids in (v, b):
        for rank, cid in enumerate(ids, start=1):
            fused[cid] = fused.get(cid, 0) + 1 / (60 + rank)
    top = sorted(fused, key=fused.get, reverse=True)

    print(f"\nQuestion: {question}")
    print(f"Chunks containing '{phrase}':")
    for c in _chunks:
        if phrase in " ".join(c["text"].lower().split()):
            cid = c["chunk_id"]
            vr = v.index(cid) + 1 if cid in v else "not in top 20"
            br = b.index(cid) + 1 if cid in b else "not in top 20"
            pos = top.index(cid) + 1 if cid in top else "-"
            print(f"  {cid}: vector rank {vr} | keyword rank {br} | position after fusion {pos}")

def union_retrieve(question, kv=8, kb=4):
    ids = list(vector_ids(question, kv))
    added = 0
    for cid in keyword_ids(question, 20):
        if added == kb:
            break
        if cid not in ids:
            ids.append(cid)
            added += 1
    return _pack(ids)


def neighbor_retrieve(question, kv=8, kb=0, radius=1):
    ids = list(vector_ids(question, kv))
    added = 0
    for cid in keyword_ids(question, 20):
        if added >= kb:
            break
        if cid not in ids:
            ids.append(cid)
            added += 1

    pos = {c["chunk_id"]: i for i, c in enumerate(_chunks)}
    wanted = set()
    for cid in ids:
        i = pos[cid]
        for j in range(i - radius, i + radius + 1):
            if 0 <= j < len(_chunks) and _chunks[j]["source"] == _chunks[i]["source"]:
                wanted.add(j)
    return _pack([_chunks[j]["chunk_id"] for j in sorted(wanted)])
if __name__ == "__main__":
    explain("Do income tax payers get PM-KISAN benefits?", "paid income tax")
    explain("Who is excluded from PM-KISAN benefits?", "retired pensioners")