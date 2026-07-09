"""Çoklu yıl trend servisi (sadece chat/Search için).

Tercih sayfası 2025 ile çalışır, ama Search'te kullanıcı
"X bölümünün son 5 yıl trendi" sorduğunda buradan veri gelir.

Veri kaynağı: data/processed/rankings_history.json (yoksa boş döner).
Format:
[
  {
    "department_code": "203910363",
    "year": 2024,
    "base_rank": 720,
    "base_score": 555.30,
    "quota": 65,
    "score_type": "SAY"
  },
  ...
]

Bu dosyayı doldurmak için yokatlas_scraper'ı 2020-2024 yıllarına genişletmek gerek
(ayrı iş, ileride). Şimdilik mantığı kuruyoruz; veri olmadığında trend "şu anki yıl" kalır.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_history() -> dict[str, list[dict]]:
    """department_code → [{year, rank, score, quota}, ...] sıralı."""
    settings = get_settings()
    history_path = Path(settings.project_root) / "data" / "processed" / "rankings_history.json"

    # Şu anki tek yıl (2025) verisini de history'e ekle ki "trend" sorulduğunda boş kalmasın
    rankings_path = Path(settings.project_root) / "data" / "processed" / "rankings.json"
    out: dict[str, list[dict]] = {}

    # 1) Mevcut yıl (2025) + içindeki history (2024, 2023)
    # BELLEK: rankings'i yeniden parse etme — recommendation'ın cache'li
    # kopyasını paylaş (ayrı yükleme ikinci bir kopya bindiriyordu)
    if rankings_path.exists():
        try:
            from unisense.application.services.recommendation_service import _load_data

            current, _, _ = _load_data()
            for r in current:
                code = str(r.get("department_code", ""))
                if not code:
                    continue
                # Bu yıl (2025)
                out.setdefault(code, []).append({
                    "year": r.get("year") or 2025,
                    "base_rank": r.get("base_rank"),
                    "base_score": r.get("base_score"),
                    "quota": r.get("quota"),
                    "score_type": r.get("score_type"),
                    "yerlesen": r.get("yerlesen"),
                })
                # Geçmiş yıllar (rankings.json içinde history alanı varsa)
                for h in (r.get("history") or []):
                    if h.get("base_rank") is None and h.get("base_score") is None:
                        continue
                    out[code].append({
                        "year": h.get("year"),
                        "base_rank": h.get("base_rank"),
                        "base_score": h.get("base_score"),
                        "yerlesen": h.get("yerlesen"),
                        "score_type": r.get("score_type"),
                    })
        except Exception as e:  # noqa: BLE001
            logger.warning("trend_load_current_failed", error=str(e)[:200])

    # 2) Geçmiş yıllar (varsa)
    if history_path.exists():
        try:
            historical = json.load(open(history_path, encoding="utf-8"))
            for r in historical:
                code = str(r.get("department_code", ""))
                if not code:
                    continue
                out.setdefault(code, []).append({
                    "year": r.get("year"),
                    "base_rank": r.get("base_rank"),
                    "base_score": r.get("base_score"),
                    "quota": r.get("quota"),
                    "score_type": r.get("score_type"),
                })
        except Exception as e:  # noqa: BLE001
            logger.warning("trend_load_history_failed", error=str(e)[:200])

    # Yıla göre sırala (en eski → en yeni)
    for code in out:
        out[code].sort(key=lambda x: x.get("year") or 0)

    return out


def get_program_trend(department_code: str) -> list[dict]:
    """Tek programın yıl-bazlı sıralama/taban trendini döner."""
    return _load_history().get(str(department_code), [])


def trend_summary(department_code: str) -> str | None:
    """Programın trendini insan dostu özetler — Search context'e enjekte için.

    Returns None: veri yok / tek yıl
    Returns str:  formatlı çoklu yıl özet
    """
    rows = get_program_trend(department_code)
    if len(rows) < 2:
        return None

    lines = ["TREND (yıllık taban):"]
    for r in rows:
        rank = r.get("base_rank")
        score = r.get("base_score")
        if rank and score:
            lines.append(
                f"  {r['year']}: sıra {int(rank):,} · taban {float(score):.2f}"
                + (f" · kontenjan {r['quota']}" if r.get('quota') else '')
            )

    # Momentum
    first = rows[0]
    last = rows[-1]
    if first.get("base_rank") and last.get("base_rank"):
        diff = first["base_rank"] - last["base_rank"]
        if abs(diff) < 100:
            momentum = "📊 stabil"
        elif diff > 0:
            momentum = f"📈 yükselişte (sıralama {abs(diff):,} iyileşmiş)"
        else:
            momentum = f"📉 düşüşte (sıralama {abs(diff):,} kötüleşmiş)"
        lines.append(f"  → {momentum}")

    return "\n".join(lines)


def has_history() -> bool:
    """rankings_history.json dosyasının var olup en az 1 ek yıl içerip içermediği."""
    settings = get_settings()
    history_path = Path(settings.project_root) / "data" / "processed" / "rankings_history.json"
    return history_path.exists() and history_path.stat().st_size > 100
