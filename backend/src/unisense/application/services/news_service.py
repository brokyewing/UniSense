"""Haber/takvim servisi — yaklaşan sınav etkinlikleri (haber akışı).

exam_calendar.json (ÖSYM/MEB 2026 kılavuz tarihleri) → 'kalan gün' hesaplı,
tarih artan sıralı yaklaşan etkinlikler. Home widget + /takvim sayfası besler.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings


@lru_cache(maxsize=1)
def _load_calendar() -> dict:
    p = Path(get_settings().project_root) / "data" / "processed" / "exam_calendar.json"
    if not p.exists():
        return {"etkinlikler": []}
    return json.load(open(p, encoding="utf-8"))


class NewsService:
    def takvim(self, limit: int = 20, gecmis: int = 3) -> dict:
        """Yaklaşan etkinlikler (kalan gün artan) + son N geçmiş etkinlik."""
        cal = _load_calendar()
        today = date.today()
        events = []
        for e in cal.get("etkinlikler", []):
            try:
                d = date.fromisoformat(e["tarih"])
            except (ValueError, KeyError):
                continue
            kalan = (d - today).days
            events.append({
                "id": e.get("id", ""),
                "sinav": e.get("sinav", ""),
                "tam_ad": e.get("tam_ad", ""),
                "tur": e.get("tur", ""),
                "tarih": e["tarih"],
                "aciklama": e.get("aciklama", ""),
                "kaynak": e.get("kaynak", ""),
                "tahmini": bool(e.get("tahmini", False)),
                "kalan_gun": kalan,
            })
        upcoming = sorted([e for e in events if e["kalan_gun"] >= 0],
                          key=lambda x: x["kalan_gun"])
        recent = sorted([e for e in events if e["kalan_gun"] < 0],
                        key=lambda x: x["kalan_gun"], reverse=True)[:gecmis]
        return {
            "guncelleme": cal.get("guncelleme", ""),
            "not": cal.get("not", ""),
            "yaklasan": upcoming[:limit],
            "gecmis": recent,
        }
