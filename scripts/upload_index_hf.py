"""Lokal ChromaDB index'ini HF dataset deposuna yükler (ücretsiz barındırma).

Kullanım:
    python scripts/upload_index_hf.py <kullanici>/unisense-index
Token: HF_TOKEN env değişkeni veya backend/.env içindeki HF_TOKEN satırı.

Veri güncellenince: lokalde `python -m unisense.cli.embed` çalıştır,
sonra bu script'i tekrar çalıştır → Render'ı redeploy et.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# chromadb/ + static_model.npz + static_tokenizer.json birlikte yüklenir
INDEX_DIR = ROOT / "backend" / "data" / "embeddings"

README = """---
license: mit
---
# UniSense Index + Statik Embedding Modeli

- `chromadb/` — önceden hesaplanmış vektör index'i (potion-multilingual, 256-dim)
- `static_model.npz` — int8 quantize edilmiş Model2Vec tablosu
- `static_tokenizer.json` — tokenizer

Boot sırasında `unisense.cli.fetch_index` indirir.
Kaynak: https://github.com/brokyewing/UniSense
"""


def _read_env_token() -> str | None:
    env_file = ROOT / "backend" / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("HF_TOKEN="):
            return line.split("=", 1)[1].strip()
    return None


def main() -> None:
    from huggingface_hub import HfApi

    token = os.environ.get("HF_TOKEN") or _read_env_token()
    if not token:
        sys.exit("HF_TOKEN gerekli (env veya backend/.env)")
    if len(sys.argv) < 2:
        sys.exit("Kullanım: python scripts/upload_index_hf.py <kullanici>/unisense-index")
    repo_id = sys.argv[1]

    if not (INDEX_DIR / "chromadb").exists():
        sys.exit(f"Index bulunamadı: {INDEX_DIR}/chromadb — önce `python -m unisense.cli.embed` çalıştır")
    if not (INDEX_DIR / "static_model.npz").exists():
        sys.exit(f"Model yok: {INDEX_DIR}/static_model.npz — önce scripts/build_static_model.py çalıştır")

    api = HfApi(token=token)
    print(f"📚 Dataset deposu: {repo_id}")
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    api.upload_file(
        path_or_fileobj=README.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )
    print(f"📤 {INDEX_DIR} yükleniyor (~372MB, birkaç dakika)...")
    api.upload_folder(
        folder_path=str(INDEX_DIR),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="index: ChromaDB + statik model güncellemesi",
        # Depo lokal klasörün aynası olsun — eski düzenden kalan dosyalar silinsin
        delete_patterns=["*"],
    )
    print(f"✅ Bitti: https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    main()
