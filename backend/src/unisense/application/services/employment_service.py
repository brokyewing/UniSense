"""Mezun istihdam servisi — TÜİK/İŞKUR verileri.

Veri: data/processed/employment_data.json (yıllık güncellenir)
Format: { "year": 2026, "items": [...], "not": "..." }
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings


@lru_cache(maxsize=1)
def _load_data() -> dict:
    p = Path(get_settings().project_root) / "data" / "processed" / "employment_data.json"
    if not p.exists():
        return {"year": 2026, "items": [], "not": "Veri henüz yüklenmedi"}
    return json.load(open(p, encoding="utf-8"))


class EmploymentService:
    def list(self, year: int | None = None, department: str | None = None) -> dict:
        """İstihdam bilgisi listesini filtrele ve döndür."""
        data = _load_data()
        items = data.get("items", [])

        if year:
            items = [i for i in items if i.get("year") == year]
        if department:
            items = [i for i in items if department.lower() in (i.get("department_name") or "").lower()]

        return {
            "year": data.get("year", 2026),
            "items": items,
            "total": len(items),
            "not": data.get("not_", data.get("not", "")),
        }

    def by_program(self, program_code: str) -> dict | None:
        """Belirli bir programın istihdam bilgisini döndür."""
        data = _load_data()
        for item in data.get("items", []):
            if item.get("program_code") == program_code:
                return item
        return None

    def years(self) -> list[int]:
        """Mevcut veri yıllarını döndür."""
        data = _load_data()
        years = set()
        for item in data.get("items", []):
            if item.get("year"):
                years.add(item["year"])
        return sorted(years, reverse=True)