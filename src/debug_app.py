from hybrid import neighbor_retrieve
from ask import label

TESTS = [
    ("who are all comes under exclusions from PM-KISAN benefits?", ["retired pensioners", "paid income tax"]),
    ("Do income tax payers get PM-KISAN benefits", ["paid income tax"]),
]

for q, phrases in TESTS:
    hits = neighbor_retrieve(q, kv=5, kb=3, radius=1)   # use the same numbers as in streamlit_app.py
    text = " ".join(" ".join(d.lower().split()) for d, _ in hits)
    print("\nQ:", q)
    print("chunks sent:", len(hits))
    print("from:", [label(m) for _, m in hits])
    for p in phrases:
        print(f"  contains '{p}':", p in text)