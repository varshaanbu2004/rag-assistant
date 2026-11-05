import sys
sys.path.insert(0, "src")

from ingest import load_chunks
from collections import Counter

chunks = load_chunks()

source_counts = Counter(c["source"] for c in chunks)

for source, count in source_counts.items():
    print(f"{source}: {count} chunks")