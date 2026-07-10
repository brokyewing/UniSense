"""DGS servisi — önlisans mezunu için lisans geçiş programları.

dgs_rankings.json (ÖSYM yıllık min/max) + departments (YÖK Atlas) birleşimi:
program kodları iki veri setinde AYNI olduğundan şehir/üniversite bilgisi
doğrudan iliştirilir. "DGS 280 puanla hangi lisans programlarına geçerim?"
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.core.text import fold_tr

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load() -> list[dict]:
    p = Path(get_settings().project_root) / "data" / "processed" / "dgs_rankings.json"
    if not p.exists():
        return []
    data = json.load(open(p, encoding="utf-8"))
    # Şehir/üni adlarını mevcut veriden iliştir (kod uzayı aynı)
    from unisense.application.services.recommendation_service import _load_data

    _, departments, uni_lookup = _load_data()
    dept_lookup = {d["code"]: d for d in departments}
    for r in data:
        d = dept_lookup.get(r["department_code"])
        if d:
            r["city"] = d.get("city", "")
            uni = uni_lookup.get(d.get("university_code", ""), {})
            r["university_name"] = uni.get("name", "")
            r["university_type"] = uni.get("type", "")
    logger.info("dgs_data_loaded", kayit=len(data))
    return data


class DgsService:
    def program_ara(
        self,
        *,
        puan_turu: str = "SAY",
        puan: float | None = None,
        bolum: str = "",
        il: str | None = None,
        limit: int = 30,
    ) -> dict:
        data = _load()
        pt = "SÖZ" if fold_tr(puan_turu) == "soz" else puan_turu.upper()
        bf = fold_tr(bolum) if bolum else ""
        ilf = fold_tr(il) if il else ""

        items = []
        for r in data:
            if r.get("puan_turu") != pt:
                continue
            if bf and bf not in fold_tr(r.get("program_adi", "")):
                continue
            if ilf and ilf != fold_tr(r.get("city", "")):
                continue
            mp = r.get("min_puan")
            if puan is not None and mp is not None and mp > puan:
                continue  # taban puanın üstünde — yerleşilemez
            items.append({
                "department_code": r["department_code"],
                "program_adi": r.get("program_adi", ""),
                "university_name": r.get("university_name", ""),
                "city": r.get("city", ""),
                "puan_turu": r.get("puan_turu", ""),
                "kontenjan": r.get("kontenjan"),
                "yerlesen": r.get("yerlesen"),
                "min_puan": mp,
                "yil": r.get("yil"),
            })

        # Tabanı puana en yakın (en "değerli" ulaşılabilir) programlar önce;
        # tabanı olmayanlar (geçen yıl boş kalanlar) sona
        items.sort(key=lambda x: (x["min_puan"] is None, -(x["min_puan"] or 0)))
        return {
            "total": len(items),
            "items": items[:limit],
            "uyari": (f"Taban puanlar {items[0]['yil'] if items else 2025} DGS "
                      "yerleştirmesine aittir; yeni dönemde değişebilir."),
        }
