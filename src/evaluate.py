import json
from ask import retrieve
from ingest import load_chunks


def norm(text):
    return " ".join(text.lower().split())


corpus = norm(" | ".join(c["text"] for c in load_chunks() if c["scheme"] == "PM-KISAN"))

with open("evaluation/test_set.json", encoding="utf-8") as f:
    TESTS = json.load(f)

# Sanity check: every key phrase must exist somewhere in your documents
for t in TESTS:
    for p in t["must_contain"]:
        if norm(p) not in corpus:
            print(f"WARNING: '{p}' (question: {t['id']}) not found in the documents")


def evaluate(name, retrieve_fn):
    print(f"\n=== {name} ===")
    scores, sizes = [], []
    for t in TESTS:
        hits = retrieve_fn(t["question"])
        sizes.append(len(hits))
        text = norm(" | ".join(doc for doc, _ in hits))
        missing = [p for p in t["must_contain"] if norm(p) not in text]
        score = 1 - len(missing) / len(t["must_contain"])
        scores.append(score)
        print(f"{t['id']:<12} {score:.0%}   missing: {missing}")
    print(f"AVERAGE: {sum(scores) / len(scores):.0%} | avg chunks sent: {sum(sizes) / len(sizes):.1f}")


if __name__ == "__main__":
    from hybrid import union_retrieve, neighbor_retrieve

    evaluate("vector, k=8", lambda q: retrieve(q, k=8))
    evaluate("union: vector 8 + keyword 4", lambda q: union_retrieve(q, kv=8, kb=4))
    evaluate("neighbors: vector 8 + keyword 4, radius 1", lambda q: neighbor_retrieve(q, kv=8, kb=4, radius=1))
    evaluate("neighbors: vector 5 + keyword 3, radius 1", lambda q: neighbor_retrieve(q, kv=5, kb=3, radius=1))
    evaluate("neighbors: vector 6 + keyword 2, radius 1", lambda q: neighbor_retrieve(q, kv=6, kb=2, radius=1))