
from hybrid import (
    _chunks,
    vector_ids,
    keyword_ids,
    neighbor_retrieve,
    combined_retrieve
)

questions = {
    "Original": "Who uploads my details for PM-KISAN, and what details must be correct?",
    "Manual": (
        "State UT Governments identify beneficiaries "
        "upload the beneficiary details on the web portal "
        "correctness of beneficiary details"
    )
}

scheme = "PM-KISAN"


def normalize(text):
    return " ".join(text.lower().split())


targets = {
    "upload": next(
        c for c in _chunks
        if "upload the beneficiary" in normalize(c["text"])
    ),
    "correctness": next(
        c for c in _chunks
        if "correctness of beneficiary" in normalize(c["text"])
    )
}


for label, question in questions.items():
    print(f"\n========== {label} ==========")

    vector = vector_ids(question, 30, scheme)
    keyword = keyword_ids(question, 30, scheme)

    for name, target in targets.items():
        cid = target["chunk_id"]

        print(f"\n{name.upper()} CHUNK:", cid)
        print("Vector rank:", vector.index(cid) + 1 if cid in vector else "Outside top 30")
        print("BM25 rank:", keyword.index(cid) + 1 if cid in keyword else "Outside top 30")

    for method_name, method in [
        ("Neighbor", neighbor_retrieve),
        ("Combined", combined_retrieve)
    ]:
        hits = method(question, scheme=scheme)

        print(f"\n{method_name} retrieval:")

        print(
            "Upload phrase:",
            any("upload the beneficiary" in normalize(doc)
                for doc, meta in hits)
        )

        print(
            "Correctness phrase:",
            any("correctness of beneficiary" in normalize(doc)
                for doc, meta in hits)
        )

        print("Total chunks:", len(hits))
