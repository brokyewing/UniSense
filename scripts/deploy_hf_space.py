"""UniSense backend'ini Hugging Face Spaces'e (Docker, free) deploy eder.

Kullanım:
    1. https://huggingface.co/settings/tokens → "write" yetkili token al
    2. set HF_TOKEN=hf_...          (PowerShell: $env:HF_TOKEN="hf_...")
    3. python scripts/deploy_hf_space.py <kullanici_adi>/unisense-api

Ne yapar:
    - Space yoksa oluşturur (Docker SDK, public)
    - backend/ içeriğini + hazır ChromaDB index'ini yükler (.env HARİÇ!)
    - HF metadata'lı README.md üretir (app_port: 8002)
    - backend/.env'deki GEMINI_API_KEYS ve FIREBASE_PROJECT_ID'yi
      Space SECRET'ı olarak, kalan config'i variable olarak ayarlar
İlk build ~5-10 dk sürer: https://huggingface.co/spaces/<space_id> → Logs
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

SPACE_README = """---
title: UniSense API
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8002
pinned: false
---

# UniSense API

Türkiye üniversite tercih asistanı — RAG backend'i.
Frontend: https://unisense.vercel.app · Kaynak: https://github.com/brokyewing/UniSense
"""

# .env'den Space SECRET'ı olarak taşınacaklar (loglarda görünmez)
SECRET_KEYS = ["GEMINI_API_KEYS", "GEMINI_API_KEY", "FIREBASE_PROJECT_ID"]
# Space variable olarak ayarlanacaklar (public config)
VARIABLES = {
    "APP_ENV": "production",
    "SECURITY_REQUIRE_AUTH": "true",
    "EMBEDDING_PROVIDER": "local",
    "RATE_LIMIT_ASK": "20",
    "RATE_LIMIT_DEFAULT": "60",
    "CORS_ALLOWED_ORIGINS": "https://unisense.vercel.app",
    # İmaja gömülü hazır index (persistent disk yok, gerek de yok)
    "CHROMA_PERSIST_DIR": "/app/data/embeddings/chromadb",
}

IGNORE = [
    ".env", ".env.*", "*.env",          # SIRLAR — asla yükleme
    "__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache",
    "logs/**", "*.log", "embed_log*", "infobox_log*",
    "_housing_probe.py", ".cache/**", "node_modules",
]


def _read_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def main() -> None:
    from huggingface_hub import HfApi

    token = os.environ.get("HF_TOKEN")
    if not token:
        sys.exit("HF_TOKEN env değişkeni gerekli (https://huggingface.co/settings/tokens — write yetkili)")
    if len(sys.argv) < 2:
        sys.exit("Kullanım: python scripts/deploy_hf_space.py <kullanici>/unisense-api")
    space_id = sys.argv[1]

    api = HfApi(token=token)

    print(f"🚀 Space: {space_id}")
    api.create_repo(space_id, repo_type="space", space_sdk="docker", exist_ok=True)

    # README (HF metadata) — backend README'sini Space'te ezer
    print("📄 README (app_port: 8002)")
    api.upload_file(
        path_or_fileobj=SPACE_README.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=space_id,
        repo_type="space",
    )

    # Backend içeriği + data (hazır chromadb index'i dahil)
    print("📦 backend/ yükleniyor (index dahil — birkaç dakika sürebilir)...")
    api.upload_folder(
        folder_path=str(BACKEND),
        repo_id=space_id,
        repo_type="space",
        ignore_patterns=IGNORE + ["README.md"],  # README'yi yukarıdaki ezmesin
        commit_message="deploy: UniSense backend + prebuilt index",
    )

    # Secrets + variables
    env = _read_env(BACKEND / ".env")
    for key in SECRET_KEYS:
        if env.get(key):
            api.add_space_secret(space_id, key, env[key])
            print(f"🔒 secret: {key} ✓")
    for key, value in VARIABLES.items():
        api.add_space_variable(space_id, key, value)
    print(f"⚙️  {len(VARIABLES)} variable ayarlandı")

    print(f"\n✅ Bitti! Build'i izle: https://huggingface.co/spaces/{space_id} → Logs")
    print(f"   API adresi: https://{space_id.replace('/', '-').replace('_', '-')}.hf.space")
    print("   Vercel'de VITE_API_URL'i bu adrese güncellemeyi unutma!")


if __name__ == "__main__":
    main()
