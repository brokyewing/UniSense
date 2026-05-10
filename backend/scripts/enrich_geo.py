"""universities.json ve departments.json'a coğrafi alanları ekle.

Çalıştır:
    python scripts/enrich_geo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Proje yolu
HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from unisense.domain.geo import (
    is_coastal_city,
    get_seas,
    get_coast_km,
    is_metropolis,
    is_central_district,
)


PROCESSED = PROJECT_ROOT / "data" / "processed"


def enrich(record: dict) -> dict:
    """Tek bir university/department dict'ine geo alanlarını ekle."""
    city = record.get("city", "")
    district = record.get("district", "")
    record["is_coastal"] = is_coastal_city(city)
    record["seas"] = get_seas(city)
    record["coast_km"] = get_coast_km(city)
    record["is_metropolis"] = is_metropolis(city)
    record["is_central_district"] = is_central_district(city, district)
    return record


def main():
    # Universities
    uni_path = PROCESSED / "universities.json"
    universities = json.load(open(uni_path, encoding="utf-8"))
    for u in universities:
        enrich(u)
    json.dump(universities, open(uni_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    coastal_count = sum(1 for u in universities if u["is_coastal"])
    metro_count = sum(1 for u in universities if u["is_metropolis"])
    central_count = sum(1 for u in universities if u["is_central_district"])

    print(f"✓ {len(universities)} üniversite enriched")
    print(f"  - Sahil ilinde: {coastal_count}")
    print(f"  - Büyükşehirde: {metro_count}")
    print(f"  - Merkez ilçede: {central_count}")

    # Departments
    dep_path = PROCESSED / "departments.json"
    departments = json.load(open(dep_path, encoding="utf-8"))
    for d in departments:
        enrich(d)
    json.dump(departments, open(dep_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"✓ {len(departments)} program enriched")

    # Örnek dağılım
    by_sea = {}
    for u in universities:
        for sea in u["seas"]:
            by_sea[sea] = by_sea.get(sea, 0) + 1
    print(f"\n  Deniz dağılımı:")
    for sea, n in sorted(by_sea.items(), key=lambda x: -x[1]):
        print(f"    {sea}: {n} üniversite")


if __name__ == "__main__":
    main()
