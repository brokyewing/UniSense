"""DGS servisi — önlisans mezunu için lisans geçiş programları.

dgs_rankings.json (ÖSYM yıllık min/max) + departments (YÖK Atlas) birleşimi:
program kodları iki veri setinde AYNI olduğundan şehir/üniversite bilgisi
doğrudan iliştirilir. "DGS 280 puanla hangi lisans programlarına geçerim?"
"""
from __future__ import annotations

import json
import re
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

    # Kod eşleşmeyen kayıtlar için üni adı → (tür, şehir) yedeği (BULGU #9):
    # dgs_rankings'in %16.7'si (1216 kayıt) departments.json koduna oturmuyordu,
    # city/university_type boş kalıp il ve vakıf/devlet filtrelerinden düşüyordu.
    uni_by_name: dict[str, tuple[str, str]] = {}
    for u in uni_lookup.values():
        nm = fold_tr(u.get("name", ""))
        if nm:
            uni_by_name[nm] = (u.get("type", ""), u.get("city", ""))

    def _match_uni(name: str) -> tuple[str, str]:
        f = fold_tr(name)
        if f in uni_by_name:
            return uni_by_name[f]
        for nm, val in uni_by_name.items():
            if f and (f.startswith(nm) or nm.startswith(f)):
                return val
        return ("", "")

    filled = 0
    for r in data:
        d = dept_lookup.get(r["department_code"])
        if d:
            r["city"] = d.get("city", "")
            uni = uni_lookup.get(d.get("university_code", ""), {})
            r["university_name"] = uni.get("name", "")
            r["university_type"] = uni.get("type", "")
            continue
        # Yedek: program_adi = "ÜNİVERSİTE ADI (ŞEHİR)/Fakülte/Bölüm..."
        pa = r.get("program_adi", "")
        uni_part = pa.split("/", 1)[0]
        m = re.search(r"\(([^)]+)\)", uni_part)
        uni_name = re.sub(r"\s*\([^)]*\)", "", uni_part).strip()
        utype, ucity = _match_uni(uni_name)
        # Şehir: parantez içinden (kendi metninden — en güvenli); yoksa üni eşleşmesi
        city = m.group(1).split("-")[-1].strip() if m else ucity
        r["university_name"] = r.get("university_name") or uni_name
        r["university_type"] = r.get("university_type") or utype
        r["city"] = r.get("city") or city
        if city or utype:
            filled += 1
    logger.info("dgs_data_loaded", kayit=len(data), yedek_dolduruldu=filled)
    return data


@lru_cache(maxsize=1)
def _load_gecis() -> list[dict]:
    p = Path(get_settings().project_root) / "data" / "processed" / "dgs_gecis.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else []


class DgsService:
    def gecis_ara(self, onlisans: str = "", limit: int = 5) -> dict:
        """Önlisans bölümü → geçilebilecek lisans bölümleri (ÖSYM Tablo-2).

        Boş sorgu → tüm önlisans program adları (autocomplete için).
        """
        gruplar = _load_gecis()
        if not onlisans.strip():
            adlar = sorted({p["ad"] for g in gruplar for p in g["programlar"] if p["ad"]})
            return {"programlar": adlar, "gruplar": []}

        q = fold_tr(onlisans)
        hits = []
        for g in gruplar:
            uyeler = [p["ad"] for p in g["programlar"]]
            skor = 0
            if q in fold_tr(g["onlisans_adi"]):
                skor = 2
            eslesen = [u for u in uyeler if q in fold_tr(u)]
            if eslesen:
                skor = max(skor, 3 if any(fold_tr(u) == q for u in eslesen) else 2)
            if skor:
                hits.append((skor, {
                    "alan": g["onlisans_adi"],
                    "eslesen_programlar": eslesen[:6] or uyeler[:6],
                    "lisans": g["lisans"],
                }))
        hits.sort(key=lambda x: -x[0])
        return {"programlar": [], "gruplar": [h[1] for h in hits[:limit]]}


    def program_ara(
        self,
        *,
        puan_turu: str = "SAY",
        puan: float | None = None,
        bolum: str = "",
        il: str | None = None,
        uni_turu: str | None = None,
        oneri: bool = False,
        limit: int = 30,
    ) -> dict:
        data = _load()
        pt = "SÖZ" if fold_tr(puan_turu) == "soz" else puan_turu.upper()
        bf = fold_tr(bolum) if bolum else ""
        ilf = fold_tr(il) if il else ""
        # Prefix eşleşme: "Vakıf" → VAKIF + VAKIF MYO; "all"/boş → filtre yok
        utf = fold_tr(uni_turu) if uni_turu and fold_tr(uni_turu) != "all" else ""

        items = []
        for r in data:
            if r.get("puan_turu") != pt:
                continue
            if bf and bf not in fold_tr(r.get("program_adi", "")):
                continue
            if ilf and ilf != fold_tr(r.get("city", "")):
                continue
            if utf and not fold_tr(r.get("university_type", "")).startswith(utf):
                continue
            mp = r.get("min_puan")
            ust_pay = 10.0 if oneri else 0.0
            if puan is not None and mp is not None and mp > puan + ust_pay:
                continue  # ulaşılamaz (öneri modunda +10'a kadar "üst seviye" sayılır)
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

        if oneri and puan is not None:
            # Öneri modu (BULGU #4): limit, üst-seviye programları alıp
            # güvenli/hedef'i kesmesin. Sıralama: (1) ULAŞILABİLİR (taban≤puan)
            # programlar önce → tabanı yüksek "değerli" olan başta; (2) üst-seviye
            # (taban puan+10'a kadar) sonra; (3) geçen yıl boş kalanlar en sonda.
            def _oneri_key(x):
                mp = x["min_puan"]
                if mp is None:
                    return (2, 0.0)
                return (0 if mp <= puan else 1, -mp)
            items.sort(key=_oneri_key)
        else:
            # Normal arama: tabanı puana en yakın (en "değerli" ulaşılabilir) önce
            items.sort(key=lambda x: (x["min_puan"] is None, -(x["min_puan"] or 0)))
        return {
            "total": len(items),
            "items": items[:limit],
            "uyari": (f"Taban puanlar {items[0]['yil'] if items else 2025} DGS "
                      "yerleştirmesine aittir; yeni dönemde değişebilir."),
        }
