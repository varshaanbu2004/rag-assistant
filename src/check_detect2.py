"""Diagnose detect_scheme behavior on test_set.json."""
import json
from hybrid import detect_scheme, SCHEME_WORDS

with open("evaluation/test_set.json", encoding="utf-8") as f:
    TESTS = json.load(f)

print("=== 1. Full detect_scheme source (including keyword lists) ===\n")
print("SCHEME_WORDS = {")
for scheme, words in SCHEME_WORDS.items():
    print(f'    "{scheme}": {words},')
print("}")

print("""
def detect_scheme(question):
    q = question.lower()
    found = {s for s, words in SCHEME_WORDS.items() if any(w in q for w in words)}
    if "PM Kisan Maan-Dhan" in found:
        found.discard("PM-KISAN")
    return found.pop() if len(found) == 1 else None
""")

print("\n=== 2. scheme=null questions: id, text, detect_scheme result, matched keyword ===\n")
for t in TESTS:
    if t.get("scheme") is None:
        q = t["question"]
        got = detect_scheme(q)
        matched = None
        for scheme, words in SCHEME_WORDS.items():
            for w in words:
                if w in q.lower():
                    matched = (scheme, w)
                    break
            if matched:
                break
        print(f"id: {t['id']}")
        print(f"  question: {q}")
        print(f"  detect_scheme returned: {got}")
        print(f"  matched keyword: {matched}")
        print()

print("=== 3. Questions where detect_scheme returned None ===\n")
for t in TESTS:
    got = detect_scheme(t["question"])
    if got is None:
        print(f"id: {t['id']}")
        print(f"  question: {t['question']}")
        print()

print("=== 4. git log -1 --oneline ===\n")
import subprocess
result = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True)
print(result.stdout.strip())