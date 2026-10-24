"""Bölüm Karşılaştırma servisi — 2-5 ÖSYM kodunu yan yana karşılaştır.

Trend, taban, sıra, kontenjan, akademik kadro, akreditasyon, burs, eğitim dili
gibi alanları toplar; frontend'de yan yana tablo gösterimi için.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from unisense.application.services.trend_service import get_program_trend
from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)

MAX_PROGRAMS = 5
MIN_PROGRAMS = 2


@lru_cache(maxsize=1)
def _load_full_data() -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    """departments + universities + rankings — code → dict lookup'ları.

    BELLEK: veriyi kendisi YÜKLEMEZ — recommendation servisinin cache'li
    (slim) yüklemesini paylaşır. Ayrı json.load, aynı verinin ikinci
    kopyasını (~190MB) yaratıp 512MB instance'ı OOM'a taşıyordu.
    """
    from unisense.application.services.recommendation_service import _load_data

    rankings, departments, uni_lookup = _load_data()
    return (
        {d["code"]: d for d in departments},
        uni_lookup,
        {r["department_code"]: r for r in rankings},
    )


@lru_cache(maxsize=1)
def _dgs_lookup() -> dict[str, dict]:
    """DGS taban verisi: department_code → kayıt.

    DGS program kodları YÖK Atlas lisans kodlarıyla AYNI olduğundan aynı
    karşılaştırma tablosunda 'DGS taban' satırı gösterilebilir — DGS'li
    kullanıcı da /karsilastir sekmesini kullanır.
    """
    p = Path(get_settings().project_root) / "data" / "processed" / "dgs_rankings.json"
    if not p.exists():
        return {}
    out: dict[str, dict] = {}
    for r in json.load(open(p, encoding="utf-8")):
        out.setdefault(str(r.get("department_code")), r)
    return out


def _program_detail(code: str) -> dict[str, Any]:
    """Tek bir program için karşılaştırma payload'ı."""
    code = str(code)
    dept_lookup, uni_lookup, rank_lookup = _load_full_data()

    dept = dept_lookup.get(code)
    if not dept:
        return {"code": code, "found": False}

    uni = uni_lookup.get(dept.get("university_code", ""), {})
    rank = rank_lookup.get(code, {})
    trend = get_program_trend(code)
    staff = dept.get("academic_staff") or {}
    dgs = _dgs_lookup().get(code)

    return {
        "code": code,
        "found": True,
        # Program
        "department_name": dept.get("name", ""),
        "department_group": dept.get("group_name", ""),
        "faculty_name": dept.get("faculty_name", ""),
        "score_type": dept.get("score_type", ""),
        "education_level": dept.get("education_level", ""),
        "education_language": dept.get("education_language", ""),
        "duration_years": dept.get("duration_years"),
        "scholarship": dept.get("scholarship", ""),
        "fee_try": dept.get("fee_try"),
        "accreditation": dept.get("accreditation", ""),
        "min_basari_sirasi_kosul": dept.get("min_basari_sirasi_kosul"),
        # Üniversite
        "university_code": dept.get("university_code", ""),
        "university_name": uni.get("name", ""),
        "university_type": uni.get("type", ""),
        "city": dept.get("city", "") or uni.get("city", ""),
        "region": dept.get("region", "") or uni.get("region", ""),
        "logo_url": uni.get("logo_url", ""),
        "website": uni.get("website", ""),
        "founded_year": uni.get("founded_year"),
        # 2025 yerleştirme
        "base_score": rank.get("base_score"),
        "base_rank": rank.get("base_rank"),
        "quota": rank.get("quota"),
        "yerlesen": rank.get("yerlesen"),
        # DGS (dikey geçiş) yerleştirme — kod eşleşirse
        "dgs_min_puan": dgs.get("min_puan") if dgs else None,
        "dgs_puan_turu": dgs.get("puan_turu") if dgs else None,
        "dgs_kontenjan": dgs.get("kontenjan") if dgs else None,
        # Akademik kadro
        "academic_total": staff.get("total", 0),
        "academic_professor": staff.get("professor", 0),
        "academic_associate": staff.get("associate_professor", 0),
        "academic_assistant": staff.get("assistant_professor", 0),
        # Trend (yıl bazlı)
        "trend": [
            {
                "year": t.get("year"),
                "base_rank": t.get("base_rank"),
                "base_score": t.get("base_score"),
                "quota": t.get("quota"),
            }
            for t in trend
        ],
        # Coğrafi
        "is_coastal": dept.get("is_coastal", False),
        "is_metropolis": dept.get("is_metropolis", False),
    }


def _highlight_diffs(items: list[dict]) -> dict[str, dict]:
    """Her sayısal alan için en iyi/en kötü değeri vurgula.

    Returns:
      {field: {best_code: <code>, worst_code: <code>}}
    """
    diffs: dict[str, dict] = {}

    # Sıralama: küçük = iyi
    # Taban: büyük = iyi
    # Kontenjan: büyük = iyi
    # Akademik toplam: büyük = iyi
    # Yerleşen: büyük = iyi
    # Ücret: küçük = iyi
    # Kuruluş yılı: küçük = "köklü" (yorum)
    rules = [
        ("base_rank",       "lower"),
        ("base_score",      "higher"),
        ("quota",           "higher"),
        ("yerlesen",        "higher"),
        ("academic_total",  "higher"),
        ("fee_try",         "lower"),
        ("founded_year",    "lower"),
    ]
    for field, mode in rules:
        valid = [(it["code"], it.get(field)) for it in items if it.get("found") and it.get(field) is not None]
        if len(valid) < 2:
            continue
        if mode == "lower":
            best = min(valid, key=lambda x: x[1])
            worst = max(valid, key=lambda x: x[1])
        else:
            best = max(valid, key=lambda x: x[1])
            worst = min(valid, key=lambda x: x[1])
        if best[1] == worst[1]:
            continue  # hepsi eşit, vurgu yok
        diffs[field] = {"best_code": best[0], "worst_code": worst[0]}

    return diffs


class CompareService:
    """Bölüm karşılaştırma orkestrasyonu."""

    def compare(self, codes: list[str]) -> dict[str, Any]:
        # Kod sayısı kontrolü
        codes_clean = [str(c).strip() for c in codes if str(c).strip()]
        codes_clean = list(dict.fromkeys(codes_clean))  # tekrarları sil, sıra koru

        if len(codes_clean) < MIN_PROGRAMS:
            return {
                "items": [],
                "diffs": {},
                "error": f"En az {MIN_PROGRAMS} program kodu gerekli.",
            }
        if len(codes_clean) > MAX_PROGRAMS:
            codes_clean = codes_clean[:MAX_PROGRAMS]

        items = [_program_detail(c) for c in codes_clean]
        diffs = _highlight_diffs(items)

        found_count = sum(1 for it in items if it.get("found"))
        logger.info(
            "compare_done",
            requested=len(codes_clean),
            found=found_count,
            diffs_count=len(diffs),
        )

        return {
            "items": items,
            "diffs": diffs,
            "error": None,
        }
