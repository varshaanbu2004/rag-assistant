from hybrid import detect_scheme

CASES = [
    ("How do I apply for crop insurance?", "PMFBY"),
    ("What is the premium for PMFBY?", "PMFBY"),
    ("How much money does PM-KISAN give per year?", "PM-KISAN"),
    ("Are retired pensioners eligible for PM-KISAN?", "PM-KISAN"),
    ("Tell me about PM Kisan Maan-Dhan pension", "PM Kisan Maan-Dhan"),
    ("Is Aadhaar compulsory?", None),
    ("Compare PM-KISAN and crop insurance", None),
]

bad = 0
for q, expected in CASES:
    got = detect_scheme(q)
    if got != expected:
        bad += 1
        print("MISMATCH:", q, "->", got, "expected", expected)
print("detect_scheme:", len(CASES) - bad, "/", len(CASES), "correct")