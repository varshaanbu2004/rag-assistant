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

Context:
{context}

Question: {question}
"""


def retrieve(question, scheme="PM-KISAN", k=8):
    search_text = question + " exclusion criteria farmer families not eligible excluded categories"
    res = collection.query(
        query_embeddings=embedder.encode([question]).tolist(),
        n_results=k,
        where={"scheme": scheme},
    )
    return list(zip(res["documents"][0], res["metadatas"][0]))


def ask(question):
    hits = retrieve(question)
    context = "\n\n".join(
        f"[{m['source']}, page {m['page']}]\n{doc}" for doc, m in hits
    )
    prompt = PROMPT.format(context=context, question=question)
    for attempt in range(3):
        try:
            return client.models.generate_content(model=MODEL_NAME, contents=prompt).text
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