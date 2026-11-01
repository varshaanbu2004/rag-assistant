import json
import os

from ask import client, MODEL_NAME

CACHE_FILE = "evaluation/rewrite_cache.json"
_cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, encoding="utf-8") as f:
        _cache = json.load(f)

REWRITE_PROMPT = """Rewrite this farmer's question using the formal wording and synonyms that an official government scheme guideline would use.
Return one line of 5 to 10 keywords only. Do not answer the question.

Question: {q}"""


def rewrite(question):
    if question in _cache:
        return _cache[question]
    try:
        text = client.models.generate_content(
            model=MODEL_NAME, contents=REWRITE_PROMPT.format(q=question)
        ).text.strip()
    except Exception as e:
        print("rewrite failed, using the original question:", str(e)[:80])
        return ""
    _cache[question] = text
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_cache, f)
    return text