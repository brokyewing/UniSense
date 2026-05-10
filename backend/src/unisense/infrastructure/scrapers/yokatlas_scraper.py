"""YÖK Atlas master scraper — RAW HTTP (Pydantic bypass).

Sorun: yokatlas-py 0.6.0 'KKTC' ve 'YURTDISI KAMU' üniversite türlerini kabul etmiyor
(Pydantic strict literal). Çözüm: alt seviye HTTP istemcisini kullan,
raw dict olarak çek, validation atla.

Çıktı:
  data/raw/yokatlas/universities.json     # 227 üni
  data/raw/yokatlas/program_groups.json   # 586 bölüm grubu
  data/raw/yokatlas/programs_2025.json    # ~12.000 program (RAW)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from yokatlas_py.http_client import HttpClient
from yokatlas_py.config import Settings

# Encoding fix for Windows console
if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


SEARCH_PATH = "/api/tercih-kilavuz/search"
UNIVERSITIES_PATH = "/api/tercih-kilavuz/universiteler"
PROGRAMS_PATH = "/api/tercih-kilavuz/universite-programlar"
CITIES_PATH = "/api/tercih-kilavuz/universite-iller"

SCORE_TYPES = ["SAY", "EA", "SÖZ", "DİL"]
PAGE_SIZE = 100
DELAY = 0.3


def _http() -> HttpClient:
    # HttpClient default Settings ile initialize edilir
    return HttpClient(settings=Settings())


def fetch_universities(http: HttpClient) -> list[dict]:
    print("\n🏛️ Üniversiteler...")
    raw = http.get_json(UNIVERSITIES_PATH)
    print(f"   ✓ {len(raw)} üniversite")
    return raw


def fetch_program_groups(http: HttpClient) -> list[dict]:
    print("\n📂 Program grupları...")
    raw = http.get_json(PROGRAMS_PATH)
    print(f"   ✓ {len(raw)} bölüm grubu")
    return raw


def fetch_score_type(http: HttpClient, score_type: str) -> list[dict]:
    """RAW JSON ile tüm programları getir, validation YOK."""
    print(f"\n📚 {score_type} programları...")
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

        total = raw.get("totalElements", 0)
        total_pages = raw.get("totalPages", 0)
        is_last = raw.get("last", False)
        print(f"   sayfa {page+1}/{total_pages} ({len(all_programs)}/{total})", end="\r")

        if is_last:
            break
        page += 1
        time.sleep(DELAY)

    print(f"\n   ✓ {score_type}: {len(all_programs)} program")
    return all_programs


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    out_dir = project_root / "data" / "raw" / "yokatlas"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎓 YÖK Atlas 2025 Master Scraper (RAW HTTP)")
    print("=" * 60)
    start = time.time()

    http = _http()

    # 1. Üniversiteler
    universities = fetch_universities(http)
    with open(out_dir / "universities.json", "w", encoding="utf-8") as f:
        json.dump(universities, f, ensure_ascii=False, indent=2)

    # 2. Program grupları
    program_groups = fetch_program_groups(http)
    with open(out_dir / "program_groups.json", "w", encoding="utf-8") as f:
        json.dump(program_groups, f, ensure_ascii=False, indent=2)

    # 3. Tüm programlar
    all_programs: list[dict] = []
    for st in SCORE_TYPES:
        progs = fetch_score_type(http, st)
        all_programs.extend(progs)
        # Ara kayıt
        with open(out_dir / "programs_2025.json", "w", encoding="utf-8") as f:
            json.dump(all_programs, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print("✅ Tamamlandı")
    print(f"   Üniversite: {len(universities)}")
    print(f"   Bölüm grubu: {len(program_groups)}")
    print(f"   Program: {len(all_programs)}")
    print(f"   Süre: {elapsed:.1f} sn")


if __name__ == "__main__":
    main()
