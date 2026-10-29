"""Analytics servisi — kullanıcı davranış analizi.

Veri: data/processed/analytics_data.json (günlük güncellenir)
Format: { "date": "2026-10-30", "events": [...], "summary": {...} }
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from unisense.core.config import get_settings


def _data_path() -> Path:
    return Path(get_settings().project_root) / "data" / "processed" / "analytics_data.json"


def _load_data() -> dict:
    p = _data_path()
    if not p.exists():
        return {"date": str(date.today()), "events": [], "summary": {}}
    try:
        return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"date": str(date.today()), "events": [], "summary": {}}


def _save_data(data: dict) -> None:
    p = _data_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class AnalyticsService:
    def log_event(self, event_type: str, page: str | None = None,
                  user_id: str | None = None, metadata: dict | None = None) -> dict:
        """Kullanıcı olayı kaydet."""
        data = _load_data()
        event = {
            "event_type": event_type,
            "page": page,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        data.setdefault("events", []).append(event)
        # Son 10000 olayı tut (bellek yönetimi)
        if len(data["events"]) > 10000:
            data["events"] = data["events"][-10000:]
        _save_data(data)
        return {"status": "ok"}

    def summary(self) -> dict:
        """Analytics özeti döndür."""
        data = _load_data()
        events = data.get("events", [])

        # Top pages
        page_counts: dict[str, int] = {}
        for e in events:
            p = e.get("page")
            if p:
                page_counts[p] = page_counts.get(p, 0) + 1
        top_pages = sorted(page_counts.items(), key=lambda x: -x[1])[:10]
        top_pages = [{"page": p, "count": c} for p, c in top_pages]

        # Top events
        event_counts: dict[str, int] = {}
        for e in events:
            et = e.get("event_type")
            if et:
                event_counts[et] = event_counts.get(et, 0) + 1
        top_events = sorted(event_counts.items(), key=lambda x: -x[1])[:10]
        top_events = [{"event": e, "count": c} for e, c in top_events]

        # Unique users
        unique_users = len({e.get("user_id") for e in events if e.get("user_id")})

        # Daily active (son 24 saat)
        today = str(date.today())
        daily_active = len({
            e.get("user_id") for e in events
            if e.get("timestamp", "").startswith(today) and e.get("user_id")
        })

        return {
            "total_events": len(events),
            "unique_users": unique_users,
            "top_pages": top_pages,
            "top_events": top_events,
            "daily_active": daily_active,
            "not": "Analytics verisi yerel dosyadan okunur. Production'da veritabanına taşınmalı.",
        }

    def clear(self) -> dict:
        """Analytics verisini temizle."""
        _save_data({"date": str(date.today()), "events": [], "summary": {}})
        return {"status": "ok", "message": "Analytics verisi temizlendi"}