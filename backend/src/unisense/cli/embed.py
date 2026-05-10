"""Embedder — chunks.json → ChromaDB.

sentence-transformers ile 384-dim embedding üretir, ChromaDB persistent store'a yazar.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "unisense"
BATCH_SIZE = 100


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    chunks_file = project_root / "data" / "processed" / "chunks.json"
    persist_dir = project_root / "data" / "embeddings" / "chromadb"
    persist_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🧠 UniSense Embedder")
    print("=" * 60)

    chunks = json.load(open(chunks_file, encoding="utf-8"))
    print(f"📥 {len(chunks)} chunk yüklendi")

    print(f"🧠 Embedding modeli yükleniyor: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"   ✓ Boyut: {model.get_sentence_embedding_dimension()}")

    print(f"💾 ChromaDB: {persist_dir}")
    client = chromadb.PersistentClient(path=str(persist_dir))

    # Collection sıfırla (idempotent)
    try:
        client.delete_collection(COLLECTION_NAME)
        print("   🗑️  Eski koleksiyon silindi")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "l2"},
    )

    print(f"\n📤 {len(chunks)} chunk embed + upload...")
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_idx:batch_idx + BATCH_SIZE]
        ids = [c["chunk_id"] for c in batch]
        documents = [c["content"] for c in batch]

        # Metadata sadece string/int/float/bool olabilir
        metadatas = []
        for c in batch:
            md = {}
            for k, v in c.items():
                if k in ("chunk_id", "content"):
                    continue
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    md[k] = v
                else:
                    md[k] = str(v)
            metadatas.append(md)

        # Embedding üret
        embeddings = model.encode(documents, convert_to_numpy=True, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        cur_batch = batch_idx // BATCH_SIZE + 1
        print(f"   batch {cur_batch}/{total_batches} ({batch_idx + len(batch)}/{len(chunks)})", end="\r")

    print()
    print(f"\n✅ {collection.count()} chunk ChromaDB'ye yüklendi")
    print(f"📁 {persist_dir}")

    # Kısa test
    print("\n🔍 Test sorgu: 'Bilgisayar Mühendisliği taban puanı'")
    q_emb = model.encode(["Bilgisayar Mühendisliği taban puanı"], convert_to_numpy=True).tolist()
    results = collection.query(
        query_embeddings=q_emb,
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        dist = results["distances"][0][i]
        print(f"\n   [{i+1}] mesafe={dist:.2f} | {meta.get('source', '?')}")
        print(f"       {doc[:200]}...")


if __name__ == "__main__":
    main()
