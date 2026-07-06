import json
import chromadb

chunks = json.load(open("data/chunks.json"))

client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_or_create_collection("standards")

BATCH = 100
for i in range(0, len(chunks), BATCH):
    batch = chunks[i:i + BATCH]
    collection.add(
        ids=[c["id"] for c in batch],
        documents=[c["text"] for c in batch],
        metadatas=[c["meta"] for c in batch],
    )
    print(f"Indexed {min(i + BATCH, len(chunks))}/{len(chunks)}")

print("Done. Collection size:", collection.count())