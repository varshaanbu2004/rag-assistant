import csv
import json
import re
import time

from ask import ask
from hybrid import combined_retrieve


def norm(text):
    return " ".join(text.lower().replace(",", "").split())


with open("evaluation/test_set.json", encoding="utf-8") as f:
    TESTS = json.load(f)

rate_limit_count = 0


def is_rate_limit(e):
    s = str(e).lower()
    return (
        "429" in s
        or "quota" in s
        or "resource_exhausted" in s
        or "too many requests" in s
        or "rate limit" in s
    )


def ask_safe(question):
    global rate_limit_count
    try:
        return ask(question, retriever=lambda q: combined_retrieve(q))
    except Exception as e:
        if is_rate_limit(e):
            rate_limit_count += 1
            if rate_limit_count >= 2:
                raise RuntimeError("stopped on second 429")
            print("  [429 hit, waiting 60s]")
            time.sleep(60)
            return ask(question, retriever=lambda q: combined_retrieve(q))
        raise


def cited_files(answer):
    out = []
    for m in re.finditer(r"\[([^\]]+)\]", answer):
        file_part = m.group(1).split(",")[0].strip()
        if file_part and not file_part.isdigit():
            out.append(file_part)
    return out


def leak_check(scheme, answer):
    prefix = "pmkisan_" if scheme == "PM-KISAN" else "pmfby_"
    return [f for f in cited_files(answer) if not f.lower().startswith(prefix)]


rows = []
leak_ids = []
stats = {"PM-KISAN": [0, 0], "PMFBY": [0, 0]}
refuse_results = {}

for t in TESTS:
    scheme = t.get("scheme")
    if scheme not in ("PM-KISAN", "PMFBY"):
        continue

    try:
        answer = ask_safe(t["question"])
    except RuntimeError as e:
        print(f"STOPPING: {e}")
        break

    text = norm(answer)

    leaks = leak_check(scheme, answer)
    if leaks:
        leak_ids.append((t["id"], leaks))

    if not t["must_contain"]:
        ok = "could not find" in text
        refuse_results[t["id"]] = "PASS" if ok else "FAIL"
    elif t.get("answer_contains"):
        missing = [p for p in t["answer_contains"] if norm(p) not in text]
        stats[scheme][0] += not missing
        stats[scheme][1] += 1

    rows.append([t["id"], scheme, answer])
    time.sleep(12)


with open("evaluation/answers_review.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows([["id", "scheme", "answer"]] + rows)

print("\n=== REPORT ===")
print(f"Leak count: {len(leak_ids)}")
for cid, leaks in leak_ids:
    print(f"  {cid}: {leaks}")
for scheme in ("PM-KISAN", "PMFBY"):
    passed, total = stats[scheme]
    print(f"{scheme} auto checks: {passed}/{total}")
print("Refusal results:")
for cid, res in refuse_results.items():
    print(f"  {cid}: {res}")