import os
import time
import chromadb
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer

load_dotenv()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
embedder = SentenceTransformer("all-MiniLM-L6-v2")
collection = chromadb.PersistentClient(path="chroma_db").get_collection("schemes")

PROMPT = """You help Indian farmers understand government schemes.
Answer ONLY from the context below. If the context does not contain the answer,
reply exactly: "I could not find this in the documents I have."
Use simple language. End with the sources you used as [file, page].
If the question asks for a list of rules or conditions, end by saying the list may be incomplete and the user should verify it on the official portal.
If the context lists several items, include every item. Check each part of the context before saying you could not find an answer.
If the context contains a rule or list that answers the question, use it. For example, if a person or group appears in a list of exclusions, say they are excluded.
When the context contains a list, include every item in it. Check all of the context before deciding the answer is missing.
Only say you could not find the answer if nothing in the context relates to the question.

Context:
{context}

Question: {question}
"""


def retrieve(question, scheme="PM-KISAN", k=6):
    search_text = question + " exclusion criteria farmer families not eligible excluded categories"
    res = collection.query(
        query_embeddings=embedder.encode([question]).tolist(),
        n_results=k,
        where={"scheme": scheme},
    )
    return list(zip(res["documents"][0], res["metadatas"][0]))


def ask(question, retriever=None):
    t0 = time.time()
    hits = (retriever or retrieve)(question)
    t1 = time.time()
    hits = (retriever or retrieve)(question)
    print("chunks sent:", len(hits), [label(m) for _, m in hits])
    context = "\n\n".join(
        f"[{m['source']}, page {m['page']}]\n{doc}" for doc, m in hits
    )
    prompt = PROMPT.format(context=context, question=question)
    for attempt in range(3):
        try:
            answer = client.models.generate_content(model=MODEL_NAME, contents=prompt).text
            t2 = time.time()
            print(f"[retrieval {t1 - t0:.1f}s | Gemini {t2 - t1:.1f}s | attempt {attempt + 1}]")
            return answer
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                time.sleep(5)
                continue
            raise
def label(m):
    p = m["page"] if m["page"] == m["page_end"] else f"{m['page']}-{m['page_end']}"
    return f"{m['source']}, page {p}"
    context = "\n\n".join(f"[{label(m)}]\n{doc}" for doc, m in hits)



if __name__ == "__main__":
    for q in [
        "How much money does PM-KISAN give per year?",
        "Who is excluded from PM-KISAN benefits?",
        "What is the cut-off date for eligibility?",
        "How do I apply for crop insurance?",
    ]:
        print("\nQ:", q)
        print(ask(q))