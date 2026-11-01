import csv
import json
import time

from ask import ask
from hybrid import neighbor_retrieve
from hybrid import combined_retrieve  

def norm(text):
    return " ".join(text.lower().replace(",", "").split())


with open("evaluation/test_set.json", encoding="utf-8") as f:
    TESTS = json.load(f)
    

rows, passed, auto_total = [], 0, 0
for t in TESTS:
    try:
        answer = ask(t["question"], retriever=lambda q: combined_retrieve(q))
    except Exception as e:
        answer = f"ERROR: {e}"
    text = norm(answer)

    if not t["must_contain"]:                       # should-refuse question/
        ok = "could not find" in text
        result = "PASS" if ok else "FAIL (should refuse)"
        auto_total += 1
        passed += ok
    elif t.get("answer_contains"):
        missing = [p for p in t["answer_contains"] if norm(p) not in text]
        result = "PASS" if not missing else f"FAIL missing: {missing}"
        auto_total += 1
        passed += not missing
    else:
        result = "MANUAL"

    print(f"{t['id']:<20} {result}")
    rows.append([t["id"], t["question"], result, answer])
    time.sleep(12)                                   # be gentle with free-tier limits

with open("evaluation/answers_review.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([["id", "question", "auto_result", "answer"]] + rows)

print(f"\nAuto-checked: {passed}/{auto_total} passed. Open evaluation/answers_review.csv for the full answers.")