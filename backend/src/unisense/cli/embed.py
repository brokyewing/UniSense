"""Embedder — chunks.json → ChromaDB (Gemini embedding API ile).

Özellikler:
- RESUME: yarıda kesilirse mevcut id'leri atlayıp kaldığı yerden devam eder
- Boyut kontrolü: koleksiyon farklı boyutta vektör içeriyorsa (eski MiniLM
  384-dim index'i gibi) koleksiyonu silip sıfırdan başlar
- Key rotasyonu + 429 backoff embeddings modülünde

Kullanım: python -m unisense.cli.embed
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import chromadb  # noqa: E402

from unisense.core.config import get_settings  # noqa: E402
from unisense.infrastructure.embeddings import embed_texts  # noqa: E402

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# Free tier: 100 embed isteği/dakika ve batch'teki HER metin ayrı istek
# sayılır. 95'lik batch + dakikalık pacing ile limitin hemen altında kal.
BATCH_SIZE = 95
MIN_BATCH_INTERVAL_S = 62.0


def _collection_dim(collection) -> int | None:
    """Koleksiyondaki mevcut vektör boyutu (boşsa None)."""
    try:
        peek = collection.get(limit=1, include=["embeddings"])
        embs = peek.get("embeddings")
        if embs is not None and len(embs) > 0:
            return len(embs[0])
    except Exception:  # noqa: BLE001
        pass
    return None


def main() -> None:
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[3]
    chunks_file = project_root / "data" / "processed" / "chunks.json"
    persist_dir = Path(settings.chroma_persist_dir)
    if not persist_dir.is_absolute():
        persist_dir = project_root / "data" / "embeddings" / "chromadb"
    persist_dir.mkdir(parents=True, exist_ok=True)

    target_dim = settings.effective_embedding_dim
    model_desc = (
        "potion-multilingual-128M (statik, lokal)"
        if settings.embedding_provider == "local"
        else f"{settings.gemini_embedding_model} (Gemini API)"
    )
    print("=" * 60)
    print("🧠 UniSense Embedder")
    print(f"   provider: {settings.embedding_provider} | model: {model_desc} | dim: {target_dim}")
    print("=" * 60)

    chunks = json.load(open(chunks_file, encoding="utf-8"))
    print(f"📥 {len(chunks)} chunk yüklendi")

    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "l2"},
    )

    # Boyut uyuşmazlığı → farklı sağlayıcıyla üretilmiş eski index → sıfırla
    existing_dim = _collection_dim(collection)
    if existing_dim is not None and existing_dim != target_dim:
        print(f"   ⚠️  Koleksiyon {existing_dim}-dim (hedef {target_dim}) — sıfırlanıyor")
        client.delete_collection(settings.chroma_collection)
        collection = client.create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "l2"},
        )

    # RESUME: mevcut id'leri atla
    existing_ids: set[str] = set()
    if collection.count() > 0:
        existing_ids = set(collection.get(include=[])["ids"])
        print(f"   ↻ Resume: {len(existing_ids)} chunk zaten mevcut, atlanacak")

    todo = [c for c in chunks if c["chunk_id"] not in existing_ids]
    if not todo:
        print(f"✅ Her şey güncel ({collection.count()} chunk)")
        return

    print(f"\n📤 {len(todo)} chunk embed + upload...")
    total_batches = (len(todo) + BATCH_SIZE - 1) // BATCH_SIZE
    start_time = time.time()

    n_keys = max(len(settings.gemini_keys_list), 1)
    for batch_idx in range(0, len(todo), BATCH_SIZE):
        batch_start_t = time.time()
        batch = todo[batch_idx:batch_idx + BATCH_SIZE]
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

        embeddings = embed_texts(documents, task_type="RETRIEVAL_DOCUMENT", max_retries=8).tolist()

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        cur_batch = batch_idx // BATCH_SIZE + 1
        elapsed = time.time() - start_time
        rate = (batch_idx + len(batch)) / max(elapsed, 1)
        eta_min = (len(todo) - batch_idx - len(batch)) / max(rate, 1) / 60
        print(
            f"   batch {cur_batch}/{total_batches} "
            f"({batch_idx + len(batch)}/{len(todo)}) — ETA ~{eta_min:.0f} dk",
            flush=True,
        )

        # RPM pacing sadece Gemini için gerekir (free tier: 100 istek/dk/key);
        # lokal ONNX'te limit yok, full hız
        if settings.embedding_provider == "gemini":
            elapsed_batch = time.time() - batch_start_t
            wait = MIN_BATCH_INTERVAL_S / n_keys - elapsed_batch
            if wait > 0 and batch_idx + BATCH_SIZE < len(todo):
                time.sleep(wait)

    print(f"\n✅ {collection.count()} chunk ChromaDB'ye yüklendi")
    print(f"📁 {persist_dir}")

    # Kısa test
    print("\n🔍 Test sorgu: 'Bilgisayar Mühendisliği taban puanı'")
    q_emb = embed_texts(["Bilgisayar Mühendisliği taban puanı"], task_type="RETRIEVAL_QUERY").tolist()
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
