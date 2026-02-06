from src.embeddings import search_similar

results = search_similar("2026 bahar döneminde dersler ne zaman başlayacak?", k=3)
for i, doc in enumerate(results):
    print(f"--- Result {i+1} ---")
    print(f"Source: {doc.metadata.get('source', '?')}")
    print(doc.page_content[:200])
    print()