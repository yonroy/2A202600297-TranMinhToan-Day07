"""
benchmark_v2.py — Chạy 5 benchmark queries tiếng Anh theo yêu cầu của nhóm E4.
"""
from __future__ import annotations
import sys
from pathlib import Path
from src.chunking import RecursiveChunker, SentenceChunker, FixedSizeChunker
from src.embeddings import LocalEmbedder, _mock_embed
from src.models import Document
from src.store import EmbeddingStore

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BOOK_FILE = "ai_engineer.md"
TOP_K = 3

BENCHMARK_QUERIES = [
    "What is the difference between language models and large language models?",
    "What are the three layers of the AI engineering stack?",
    "How does RAG help ground LLM outputs in external knowledge?",
    "What are the main trade-offs between fine-tuning and prompt engineering?",
    "What is LLM-as-a-judge and when is it useful?",
]

def load_book(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def build_store(text: str, chunker, embedder) -> EmbeddingStore:
    store = EmbeddingStore(collection_name="temp", embedding_fn=embedder)
    raw_chunks = chunker.chunk(text)
    docs = []
    for i, content in enumerate(raw_chunks):
        # Giả lập metadata: nếu ở 10% đầu sách thì coi là Chapter 1
        chapter = "chapter1" if i < (len(raw_chunks) // 10) else "other"
        docs.append(Document(id=f"doc_{i}", content=content, metadata={"part": chapter}))
    store.add_documents(docs)
    return store

def main():
    text = load_book(BOOK_FILE)
    try:
        embedder = LocalEmbedder()
    except:
        embedder = _mock_embed

    # Sử dụng RecursiveChunker làm strategy chính (vì nó cho kết quả tốt nhất ở lần chạy trước)
    chunker = RecursiveChunker(chunk_size=500)
    store = build_store(text, chunker, embedder)

    print(f"Results for Group E4 Coordination:")
    print(f"Strategy: Recursive (size=500)")
    print("-" * 40)

    for i, query in enumerate(BENCHMARK_QUERIES, 1):
        print(f"Q{i}: {query}")
        if i == 2:
            # Query 2 kèm metadata filter
            results = store.search_with_filter(query, top_k=TOP_K, metadata_filter={"part": "chapter1"})
            print(f"   (Used metadata filter: {{'part': 'chapter1'}})")
        else:
            results = store.search(query, top_k=TOP_K)
        
        for idx, r in enumerate(results, 1):
            print(f"   [{idx}] score={r['score']:.4f} snippet: {r['content'][:100].strip()}...")
    
    # Baseline comparison for the report
    stats = {}
    for name, c in {"fixed_size": FixedSizeChunker(500), "by_sentences": SentenceChunker(3), "recursive": RecursiveChunker(chunk_size=500)}.items():
        chks = c.chunk(text[:50000]) # 50k chars baseline
        stats[name] = {"count": len(chks), "avg": sum(len(x) for x in chks)/len(chks)}
    
    print("\nBaseline Stats (50k chars):")
    for k, v in stats.items():
        print(f"  {k}: count={v['count']}, avg_len={v['avg']:.1f}")

if __name__ == "__main__":
    main()
