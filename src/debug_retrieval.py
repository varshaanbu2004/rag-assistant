from ask import retrieve, label

QUESTION = "Who is excluded from PM-KISAN benefits?"

for doc, m in retrieve(QUESTION, k=4):
    print("\n[", label(m), "] length:", len(doc))
    print("has 'constitutional':", "constitutional" in doc.lower())
    print("has 'Local Bodies':", "local bodies" in doc.lower())
    print(doc[:300])