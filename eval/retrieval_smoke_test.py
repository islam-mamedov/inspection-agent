import chromadb

client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_collection("standards")

QUESTIONS = [
    "What causes D-cracking in concrete?",
    "How do I determine whether a crack is active or dormant?",
    "What repair methods are suitable for dormant cracks?",
    "What surface preparation is required before concrete repair?",
    "What is alkali-carbonate reaction?",
    "How should core samples be taken from damaged concrete?",
    "What materials are used for underwater concrete repair?",
    "When is epoxy injection an appropriate repair method?",
    "What causes freezing and thawing damage in concrete?",
    "How is spalling different from scaling?",
]

for q in QUESTIONS:
    res = collection.query(query_texts=[q], n_results=3)
    print("=" * 70)
    print("Q:", q)
    for doc_id, doc in zip(res["ids"][0], res["documents"][0]):
        print(f"  [{doc_id}] {doc[:150].replace(chr(10), ' ')}")