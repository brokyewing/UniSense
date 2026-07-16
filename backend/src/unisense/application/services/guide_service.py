"""Bölüm rehberi servisi — gezilebilir /bolum katalog + detay.

dept_guides.json (AI bölüm tanıtımı) + departments/rankings birleşimi:
"[bölüm] ne iş yapar" içeriği + o bölümü veren tüm üniversitelerin canlı
taban puanı/sıralaması. Hem retention (öğrenci İŞKUR'a gitmesin) hem SEO
içerik sayfalarının kaynağı.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.text import fold_tr


def slugify(name: str) -> str:
    """'Bilgisayar Programcılığı' → 'bilgisayar-programciligi' (URL-güvenli)."""
    s = fold_tr(name)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


@lru_cache(maxsize=1)
def _load_guides() -> dict[str, dict]:
    p = Path(get_settings().project_root) / "data" / "processed" / "dept_guides.json"
    if not p.exists():
        return {}
    guides = json.load(open(p, encoding="utf-8"))
    return {slugify(g["name"]): g for g in guides}


def _summary(content: str, limit: int = 200) -> str:
    """İçerikten kısa özet (katalog kartı + meta description için)."""
    text = re.sub(r"[*#>_`]", "", content or "")
    text = re.sub(r"[\U0001F000-\U0001FAFF☀-➿]", "", text)  # emoji temizle
    m = re.search(r"Bölüm Nedir[:\s]*(.+)", text, re.S)
    body = m.group(1) if m else text
    body = " ".join(body.split())
    return body[:limit].rstrip() + ("…" if len(body) > limit else "")


class GuideService:
    def list_guides(self) -> list[dict]:
        guides = _load_guides()
        out = [
            {
                "slug": slug,
                "name": g["name"],
                "category": g.get("category", ""),
                "program_count": g.get("program_count", 0),
                "summary": _summary(g.get("content", "")),
            }
            for slug, g in guides.items()
        ]
        out.sort(key=lambda x: fold_tr(x["name"]))
        return out

    def get_guide(self, slug: str) -> dict | None:
        guides = _load_guides()
        g = guides.get(slug)
        if not g:
            return None
        # O bölümü veren tüm programlar + canlı taban/sıra
        from unisense.application.services.recommendation_service import _load_data

        rankings, departments, uni_lookup = _load_data()
        rank_by_code = {r["department_code"]: r for r in rankings}
        programs = []
        seen: set[str] = set()  # departments.json'da bazı kodlar tekrar ediyor — tekilleştir
        for d in departments:
            if d.get("group_name") != g["name"]:
                continue
            if d["code"] in seen:
                continue
            seen.add(d["code"])
            r = rank_by_code.get(d["code"], {})
            uni = uni_lookup.get(d["university_code"], {})
            programs.append({
                "department_code": d["code"],
                "university_name": uni.get("name", ""),
                "university_type": uni.get("type", ""),
                "city": d.get("city", ""),
                "score_type": d.get("score_type", ""),
                "base_score": r.get("base_score"),
                "base_rank": r.get("base_rank"),
                "quota": r.get("quota"),
                "scholarship": d.get("scholarship", ""),
                "education_language": d.get("education_language", ""),
            })
        # Tabanı yüksek (en zor/prestijli) önce; tabanı olmayan (boş kalan) sona
        programs.sort(key=lambda x: (x["base_score"] is None, -(x["base_score"] or 0)))
        # Veri yılı — frontend '(YYYY yerleştirme)' etiketini veriden okusun
        yillar = {r.get("year") for r in rankings[:500] if r.get("year")}
        return {
            "slug": slug,
            "data_yili": max(yillar) if yillar else None,
            "name": g["name"],
            "category": g.get("category", ""),
            "program_count": g.get("program_count", 0),
            "summary": _summary(g.get("content", "")),
            "content": g.get("content", ""),
            "programs": programs,
        }
