"""YÖK Atlas Ek Veri Scraper — Önlisans + DGS.

KEŞİF: yokatlas-py 0.6.0 sadece SAY/EA/SÖZ/DİL puan türlerini destekliyor.
Aynı API endpoint (`/api/tercih-kilavuz/search`) `puanTuru=TYT` filter'ı
ile **önlisans** verisini döner — sadece ana scraper'da TYT eksikti.

DGS için ayrı endpoint denenmeli (henüz keşfedilmedi).

Trend için scrape GEREKMİYOR — mevcut response'da `minPuan1/2`,
`basariSirasi1/2`, `gk1/2` field'ları zaten 2024 ve 2023 verisi içerir.
transform_yokatlas.py güncellendi → otomatik history alanına yansır.

Çalıştır:
    python -m unisense.infrastructure.scrapers.yokatlas_extra_scraper --target onlisans
    python -m unisense.infrastructure.scrapers.yokatlas_extra_scraper --target dgs

Çıktı:
    data/raw/yokatlas/programs_onlisans_2025.json   # ~9300 program
    data/raw/yokatlas/programs_dgs_2025.json        # eksik (deneysel)

Sonra transform_yokatlas.py çalıştırılarak processed/'a aktarılır.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from yokatlas_py.http_client import HttpClient
from yokatlas_py.config import Settings

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


SEARCH_PATH = "/api/tercih-kilavuz/search"
PAGE_SIZE = 100
DELAY = 0.3

HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[4]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "yokatlas"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _http() -> HttpClient:
    return HttpClient(settings=Settings())


def fetch_score_type(http: HttpClient, score_type: str, label: str) -> list[dict]:
    """Sayfalı arama — yokatlas-py search API'sine puanTuru filter ile."""
    print(f"\n📚 {label} programları (puan türü = {score_type})")
    all_programs: list[dict] = []
    page = 0
    while True:
        body = {
            "filters": {"puanTuru": score_type},
            "page": page,
            "size": PAGE_SIZE,
            "sortBy": "basariSirasi",
            "direction": "ASC",
        }
        try:
            raw = http.post_json(SEARCH_PATH, json_body=body)
        except Exception as e:
            print(f"   [hata] sayfa {page}: {e}")
            break

        items = raw.get("content", [])
        if not items:
            break

        all_programs.extend(items)
        total = raw.get("totalElements") or "?"
        print(f"   sayfa {page}: +{len(items)} (toplam {len(all_programs)}/{total})")

        if len(all_programs) >= (raw.get("totalElements") or 0):
            break
        page += 1
        time.sleep(DELAY)
    return all_programs


def main():
    p = argparse.ArgumentParser(description="YÖK Atlas — Önlisans/DGS scraper")
    p.add_argument("--target", required=True, choices=["onlisans", "dgs"])
    p.add_argument("--max-pages", type=int, default=200)
    args = p.parse_args()

    http = _http()
    try:
        if args.target == "onlisans":
            data = fetch_score_type(http, "TYT", "Önlisans (2 yıllık)")
            out_path = DATA_DIR / "programs_onlisans_2025.json"
        elif args.target == "dgs":
            # DGS için puanTuru=DGS denemesi
            print("\n⚠️ DGS endpoint deneysel — yokatlas-py'da resmi destek yok.")
            data = fetch_score_type(http, "DGS", "DGS (Önlisans→Lisans)")
            if not data:
                print("\n❌ DGS verisi alınamadı. ÖSYM Tercih Kılavuzu PDF'inden manuel çekme gerek.")
                print("   Alternatif: https://yokatlas.yok.gov.tr/dgs-tercih-sihirbazi.php (HTML scrape)")
            out_path = DATA_DIR / "programs_dgs_2025.json"

        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✓ {len(data)} kayıt → {out_path}")
        print(f"  Boyut: {out_path.stat().st_size // 1024} KB")
        print("\nSonra şunu çalıştır:")
        print("  python -m unisense.infrastructure.scrapers.transform_yokatlas")
        print("(önlisans/DGS için transform genişletilmesi gerekebilir)")
    finally:
        http.close()


if __name__ == "__main__":
    main()
