import re
from rank_bm25 import BM25Okapi
from ask import embedder, collection
from ingest import load_chunks

STOP = {"the", "a", "an", "is", "are", "of", "to", "for", "do", "does", "what",
        "who", "how", "in", "on", "and", "or", "get", "can", "i", "be", "by", "from"}


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


# Keyword index built in memory from the same chunks as the vector index
_chunks = load_chunks()
_by_id = {c["chunk_id"]: c for c in _chunks}
_bm25 = BM25Okapi([tokens(c["text"]) for c in _chunks])

SCHEME_WORDS = {
    "PMFBY": ["pmfby", "fasal bima", "crop insurance", "insurance", "crop loss"],
    "PM-KISAN": ["pm-kisan", "pm kisan", "pmkisan", "kisan samman"],
    "PM Kisan Maan-Dhan": ["maan-dhan", "maandhan", "maan dhan", "pm-kmy", "pmkmy"],
}

def detect_scheme(question):
    q = question.lower()
    found = {s for s, words in SCHEME_WORDS.items() if any(w in q for w in words)}
    if "PM Kisan Maan-Dhan" in found:
        found.discard("PM-KISAN")          # "PM Kisan Maan-Dhan" contains "pm kisan"
    return found.pop() if len(found) == 1 else None


def _meta(c):
    return {"source": c["source"], "page": c["page"],
            "page_end": c["page_end"], "scheme": c["scheme"]}


def _pack(ids):
    return [(_by_id[i]["text"], _meta(_by_id[i])) for i in ids]


def keyword_ids(question, n=20, scheme=None):
    scores = _bm25.get_scores(tokens(question))
    order = sorted(range(len(_chunks)), key=lambda i: scores[i], reverse=True)
    out = []
    for i in order:
        if scores[i] <= 0 or len(out) >= n:
            break
        if scheme and _chunks[i]["scheme"] != scheme:
            continue
        out.append(_chunks[i]["chunk_id"])
    return out

def vector_ids(question, n=20, scheme=None):
    extra = {"where": {"scheme": scheme}} if scheme else {}
    res = collection.query(
        query_embeddings=embedder.encode([question]).tolist(),
        n_results=n * 3,
        **extra,
    )
    out = []
    for cid, meta in zip(res["ids"][0], res["metadatas"][0]):
        out.append(cid)
        if len(out) >= n:
            break
    return out


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


def neighbor_retrieve(question, kv=8, kb=4, radius=1, scheme=None):
    scheme = scheme or detect_scheme(question)
    # Tier 1: top vector hits (ranks 1-kv) + keyword hits, expanded with neighbors
    v_all = vector_ids(question, 30, scheme)
    tier1 = list(v_all[:kv])
    added = 0
    for cid in keyword_ids(question, 50, scheme):
        if added >= kb:
            break
        if cid not in tier1:
            tier1.append(cid)
            added += 1
    pos = {c["chunk_id"]: i for i, c in enumerate(_chunks)}
    wanted_idx = set()
    for cid in tier1:
        i = pos[cid]
        for j in range(i - radius, i + radius + 1):
            if 0 <= j < len(_chunks) and _chunks[j]["source"] == _chunks[i]["source"]:
                wanted_idx.add(j)
    # Tier 2: vector ranks 9-30 added alone (no neighbors), keeps scheme filter
    tier1_ids = {_chunks[j]["chunk_id"] for j in wanted_idx}
    tier2 = [cid for cid in v_all[kv:30] if cid not in tier1_ids]
    all_ids = list(tier1_ids | set(tier2))
    all_ids.sort(key=lambda cid: pos[cid])
    return _pack(all_ids)


def inspect_target_chunks(question, target_ids):
    v = vector_ids(question, 30)
    b = keyword_ids(question, 30)

    print(f"\nQUESTION: {question}")

    for cid in target_ids:
        vr = v.index(cid) + 1 if cid in v else "Not in top 30"
        br = b.index(cid) + 1 if cid in b else "Not in top 30"

        print(f"{cid}: Vector rank = {vr}, BM25 rank = {br}")
def inspect_union(question, kv=8, kb=4):
    results = union_retrieve(question, kv, kb)

    print(f"\nUNION RESULTS: {question}")

    for i, (chunk, meta) in enumerate(results, start=1):
        print(
            f"\n{i}. {meta['source']} | "
            f"Page {meta['page']}-{meta['page_end']}"
        )
        print(chunk[:300])
from rewrite import rewrite
def rewritten_retrieve(question, kv=8, kb=4, radius=1, scheme=None):
    scheme = scheme or detect_scheme(question)
    rewritten = (rewrite(question) or "").strip()
    if not rewritten:
        return neighbor_retrieve(question, kv, kb, radius, scheme)
    expanded = f"{question} {rewritten}"
    return neighbor_retrieve(expanded, kv, kb, radius, scheme)

def _merge_for_scheme(question, rewrite_text, kv, kb, radius, scheme):
    """Merge the original-question and rewritten-question retrieval paths for
    one scheme. `rewrite_text` is computed once by the caller, so no extra
    Gemini calls are made."""
    seen, merged = set(), []
    for q in (question, f"{question} {rewrite_text}" if rewrite_text else question):
        for doc, meta in neighbor_retrieve(q, kv, kb, radius, scheme):
            if doc not in seen:
                seen.add(doc)
                merged.append((doc, meta))
    return merged


def combined_retrieve(question, kv=8, kb=4, radius=1, scheme=None):
    scheme = scheme or detect_scheme(question)
    order = {c["text"]: i for i, c in enumerate(_chunks)}
    if scheme:
        # Scheme detected: existing behavior, one Gemini rewrite call per question.
        rewrite_text = (rewrite(question) or "").strip()
        merged = _merge_for_scheme(question, rewrite_text, kv, kb, radius, scheme)
    else:
        # No scheme detected: try both schemes once each with a smaller
        # candidate set, interleave hits in relevance order, cap at 40,
        # then sort by chunk position at the end for display.
        rewrite_text = (rewrite(question) or "").strip()
        seen, merged = set(), []
        for s in ("PM-KISAN", "PMFBY"):
            for doc, meta in _merge_for_scheme(question, rewrite_text, 5, 2, 1, s):
                if doc not in seen:
                    seen.add(doc)
                    merged.append((doc, meta))
        merged = merged[:40]
    merged.sort(key=lambda h: order.get(h[0], 0))
    return merged

if __name__ == "__main__":
    explain("Do income tax payers get PM-KISAN benefits?", "paid income tax")
    explain("Who is excluded from PM-KISAN benefits?", "retired pensioners")
    print("\n========== SOURCE PASSAGE CHECK ==========")
    inspect_target_chunks(
        "Who is excluded from PM-KISAN benefits?",
        ["pmkisan_guidelines_rev2020_c2",
         "pmkisan_guidelines_rev2020_c3"]
    )

    inspect_target_chunks(
        "What can eligible farmers do if they are excluded from PM-KISAN?",
        ["pmkisan_guidelines_rev2020_c22"]
    )
    inspect_union(
        "Who is excluded from PM-KISAN benefits?"
    )

    inspect_union(
        "What can eligible farmers do if they are excluded from PM-KISAN?"
    )

    search_terms = [
        "institutional land",
        "constitutional posts",
        "serving or retired officers",
        "paid income tax",
        "opportunity to represent their case",
        "eligible but have been excluded"
    ]


    for term in search_terms:
        print(f"\nSearching for: {term}")
        found = False

        for c in _chunks:
            if term.lower() in c["text"].lower():
                found = True
                print(
                    f"Found in {c['chunk_id']} | "
                    f"Page: {c['page']}-{c['page_end']}"
                )
                print(c["text"][:500])

        if not found:
            print("NOT FOUND IN LOADED CHUNKS")

        print("\n========== FULL EXCLUSION CHUNKS ==========")

    for cid in ["pmkisan_guidelines_rev2020_c2",
                "pmkisan_guidelines_rev2020_c3",
                "pmkisan_guidelines_rev2020_c22"]:

        if cid in _by_id:
            print(f"\n\n===== {cid} =====")
            print(_by_id[cid]["text"])