"""Compare detect_scheme(question) against the 'scheme' field in evaluation/test_set.json."""
import json

from hybrid import detect_scheme

with open("evaluation/test_set.json", encoding="utf-8") as f:
    TESTS = json.load(f)

counts = {"PM-KISAN": [0, 0], "PMFBY": [0, 0], None: [0, 0]}
wrong = []

for t in TESTS:
    expected = t.get("scheme")
    got = detect_scheme(t["question"])
    bucket = expected if expected in counts else None
    if bucket is None:
        continue
    counts[bucket][1] += 1
    if got == expected:
        counts[bucket][0] += 1
    else:
        wrong.append((t["id"], expected, got))

print("Correct / total:")
for scheme in ("PM-KISAN", "PMFBY", None):
    correct, total = counts[scheme]
    label = "scheme=None" if scheme is None else scheme
    print(f"  {label:<10} {correct}/{total}")

print()
print("Ids where detect_scheme returned None or the wrong scheme:")
for cid, expected, got in wrong:
    print(f"  {cid:<30} expected={expected} got={got}")