"""universities.json'ı Wikipedia infobox verisiyle zenginleştir.

Girdi:
  - data/processed/universities.json (mevcut)
  - data/raw/wikipedia/infobox.json (yeni — wikipedia_infobox_scraper çıktısı)

Çıktı:
  - data/processed/universities.json — şu yeni alanlarla:
    website, founded_year, logo_url, phone, email, address, rector,
    wiki_type, wiki_short_name

Kullanım:
  python -m unisense.infrastructure.scrapers.enrich_universities
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# Infobox key → universities.json field eşlemesi
FIELD_MAP = {
    "website": "website",
    "founded_year": "founded_year",
    "logo_raw": "logo_url",
    "phone": "phone",
    "email": "email",
    "address": "address",
    "rector": "rector",
    "founder": "founder",
    "type_wiki": "wiki_type",
    "short_name_wiki": "wiki_short_name",
    "colors": "colors",
    "student_count_raw": "student_count_raw",
}


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    unis_file = project_root / "data" / "processed" / "universities.json"
    infobox_file = project_root / "data" / "raw" / "wikipedia" / "infobox.json"

    if not unis_file.exists():
        print(f"❌ {unis_file} bulunamadı.")
        return
    if not infobox_file.exists():
        print(f"❌ {infobox_file} bulunamadı. Önce wikipedia_infobox_scraper çalıştır.")
        return

    universities = json.load(open(unis_file, encoding="utf-8"))
    infobox_data = json.load(open(infobox_file, encoding="utf-8"))
    infobox_by_code = {x["code"]: x.get("infobox", {}) for x in infobox_data}

    print("=" * 60)
    print("🔨 UniSense Enricher")
    print("=" * 60)
    print(f"📥 {len(universities)} üni, {len(infobox_by_code)} infobox kaydı")

    enriched_count = 0
    field_counts: dict[str, int] = {v: 0 for v in FIELD_MAP.values()}

    for u in universities:
        code = u["code"]
        ib = infobox_by_code.get(code, {})
        if not ib:
            continue

        added_any = False
        for ib_key, field in FIELD_MAP.items():
            value = ib.get(ib_key)
            if value is None or value == "":
                continue
            # Sadece boş/eksikse yaz (mevcut veriyi ezme)
            if u.get(field) in (None, "", 0):
                u[field] = value
                field_counts[field] += 1
                added_any = True

        if added_any:
            enriched_count += 1

    # Yaz
    with open(unis_file, "w", encoding="utf-8") as f:
        json.dump(universities, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {enriched_count}/{len(universities)} üniversite zenginleştirildi")
    print("\n📊 Eklenen alan sayıları:")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"   {field:20s}: {count}")

    print(f"\n📁 {unis_file}")


if __name__ == "__main__":
    main()
