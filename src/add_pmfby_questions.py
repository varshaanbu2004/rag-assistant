import json
import shutil

from ingest import load_chunks


def norm(t):
    return " ".join(t.lower().split())


CHUNKS = [(c["source"], norm(c["text"])) for c in load_chunks()]


def found(phrase, prefix):
    p = norm(phrase)
    return any(src.startswith(prefix) and p in txt for src, txt in CHUNKS)


# (id, question, scheme, file prefix, tag, candidate phrases in order of preference)
Q = [
    ("pmfby_risks", "Which risks are covered under PMFBY crop insurance?", "PMFBY", "pmfby_", "direct",
     ["prevented sowing", "localized calamities", "post-harvest losses", "mid-season adversity"]),
    ("pmfby_premium", "How much premium does a farmer pay for crop insurance under PMFBY?", "PMFBY", "pmfby_", "direct",
     ["1.5%", "2% for", "5% for", "farmer premium"]),
    ("pmfby_cutoff", "What is the last date to enrol for crop insurance?", "PMFBY", "pmfby_", "direct",
     ["cut-off date", "cut off date", "31st july", "31 july", "31st december"]),
    ("pmfby_report_loss", "How do I report crop damage from hailstorm or flooding?", "PMFBY", "pmfby_", "direct",
     ["72 hours", "localized calamities", "inundation"]),
    ("pmfby_eligibility", "Who can enrol for PMFBY?", "PMFBY", "pmfby_", "direct",
     ["non-loanee", "loanee farmers", "sharecroppers", "tenant"]),
    ("pmfby_flood_rephrased", "My crop got destroyed by flood. Do I get insurance money?", "PMFBY", "pmfby_", "rephrased",
     ["inundation", "localized calamities", "72 hours"]),
    ("pmfby_premium_rephrased", "How much money do I have to pay to insure my wheat?", "PMFBY", "pmfby_", "rephrased",
     ["1.5%", "2% for", "5% for"]),
    ("pmfby_loan_rephrased", "I took a crop loan. Is insurance automatic for me?", "PMFBY", "pmfby_", "rephrased",
     ["loanee farmers", "non-loanee", "voluntary"]),
    ("pmfby_unseen_sowing", "What happens if my crop fails to sprout because of drought at sowing time?", "PMFBY", "pmfby_", "unseen",
     ["prevented sowing"]),
    ("pmfby_unseen_postharvest", "Is there compensation if my cut crop gets wet in the rain after harvest?", "PMFBY", "pmfby_", "unseen",
     ["post-harvest losses", "post harvest losses", "14 days"]),
    ("refuse_tractor_loan", "How do I get a loan to buy a tractor?", None, "pmfby_", "refuse", []),
    ("refuse_mgnrega", "How many days of paid work does MGNREGA guarantee?", None, "pmfby_", "refuse", []),
    ("cross_apply_insurance", "How do I apply for crop insurance?", None, "pmfby_", "cross",
     ["national crop insurance portal", "crop insurance portal", "common service"]),
    ("cross_aadhaar_insurance", "Do I need Aadhaar for crop insurance?", None, "pmfby_", "cross",
     ["aadhaar"]),
    ("cross_aadhaar_noscheme", "Is Aadhaar compulsory?", None, "pmkisan_", "cross",
     ["aadhaar seeded"]),
]

path = "evaluation/test_set.json"
shutil.copy(path, "evaluation/test_set.backup.json")
with open(path, encoding="utf-8") as f:
    tests = json.load(f)
have = {t["id"] for t in tests}

for qid, question, scheme, prefix, tag, cands in Q:
    if qid in have:
        print("exists, skipped:", qid)
        continue
    keep = [p for p in cands if found(p, prefix)][:2]
    if cands and not keep:
        print("SKIPPED (no candidate phrase found in the PDF):", qid)
        continue
    tests.append({"id": qid, "question": question, "must_contain": keep, "scheme": scheme, "tag": tag})
    print("ADDED", qid, keep)

with open(path, "w", encoding="utf-8") as f:
    json.dump(tests, f, indent=2, ensure_ascii=False)
print("total questions:", len(tests))