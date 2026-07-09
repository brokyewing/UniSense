"""Hazır ChromaDB index'ini HF dataset deposundan indirir.

Render free tier'da kalıcı disk yok; index her boot'ta yeniden embed etmek
yerine (dakikalar) HF'den indirilir (~30-60 sn). Dataset depoları HF'de
ücretsizdir ve public depo için token gerekmez.

Kullanım: HF_INDEX_REPO=BrokyEwing/unisense-index python -m unisense.cli.fetch_index
Index zaten doluysa hiçbir şey yapmaz (idempotent).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    repo = os.environ.get("HF_INDEX_REPO", "").strip()
    if not repo:
        print("HF_INDEX_REPO tanımlı değil — index indirme atlandı")
        return 1

    persist_dir = Path(os.environ.get("CHROMA_PERSIST_DIR", "./data/embeddings/chromadb"))
    if persist_dir.exists() and any(persist_dir.iterdir()):
        print(f"Index zaten mevcut: {persist_dir} — indirme atlandı")
        return 0

    from huggingface_hub import snapshot_download

    print(f">>> Index indiriliyor: {repo} → {persist_dir}")
    persist_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo,
        repo_type="dataset",
        local_dir=str(persist_dir),
        # .gitattributes vb. depo metadata'sını alma
        ignore_patterns=[".gitattributes", "README.md"],
    )
    n_files = sum(1 for _ in persist_dir.rglob("*") if _.is_file())
    print(f">>> İndirme tamam: {n_files} dosya")
    return 0


if __name__ == "__main__":
    sys.exit(main())
