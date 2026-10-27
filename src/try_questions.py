from hybrid import neighbor_retrieve
from ask import ask

QUESTIONS = [
    "Who is excluded from PM-KISAN benefits?"
]

for q in QUESTIONS:
    print("\nQ:", q)
    print(ask(q, retriever=lambda x: neighbor_retrieve(x, kv=5, kb=3, radius=1)))

from hybrid import _chunks, _pack
from hybrid import _chunks
i = next(n for n, c in enumerate(_chunks) if "paid income tax" in " ".join(c["text"].lower().split()))
print(_chunks[i]["text"][:500])

i = next(n for n, c in enumerate(_chunks) if "paid income tax" in " ".join(c["text"].lower().split()))
ids = [_chunks[j]["chunk_id"] for j in range(i - 1, i + 2)]
print("Isolation chunks:", ids)
print(ask("Do income tax payers get PM-KISAN benefits?", retriever=lambda q: _pack(ids)))