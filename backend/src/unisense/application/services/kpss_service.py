"""KPSS servisi — bölüm → başvurulabilir kadrolar + geçmiş taban puanlar.

Veri:
  kpss_kadrolar.json    — aktif tercih dönemi (2026/1) kadroları + nitelik kodları
  kpss_nitelikler.json  — nitelik kodu → öğrenim şartı açıklaması
  kpss_placements.json  — geçmiş yerleştirme taban puanları (2025/1, 2025/2)

"Bilgisayar mühendisi hangi kadrolara başvurabilir?" → bölüm adı nitelik
açıklamalarında aranır (fold'lu), eşleşen kodların kadroları + herkese açık
kodlar ("Herhangi bir lisans programından mezun olmak") birleştirilir.
Geçmiş taban, kurum+unvan+il eşleşmesiyle iliştirilir (kadro kodları
dönemler arası değiştiği için ad bazlı yaklaşık eşleme).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.core.text import fold_tr

logger = get_logger(__name__)

# "Herhangi bir X programından mezun" kalıbı — bölüm fark etmeksizin uygun
_GENERIC_HINTS = ("herhangi bir lisans", "herhangi bir onlisans",
                  "herhangi bir on lisans", "herhangi bir ortaogretim",
                  "lise ve dengi")


@lru_cache(maxsize=1)
def _load() -> tuple[list[dict], dict[str, dict], list[dict]]:
    proc = Path(get_settings().project_root) / "data" / "processed"

    def _j(name: str, default):
        p = proc / name
        return json.load(open(p, encoding="utf-8")) if p.exists() else default

    kadrolar = _j("kpss_kadrolar.json", [])
    nitelikler = _j("kpss_nitelikler.json", {})
    placements = _j("kpss_placements.json", [])
    logger.info("kpss_data_loaded", kadro=len(kadrolar),
                nitelik=len(nitelikler), gecmis=len(placements))
    return kadrolar, nitelikler, placements


# Kılavuzda kurum adının sonuna yapışan statü ifadeleri (taban eşleşmesi için temizlenir)
_STATU_SUFFIXES = (
    "kit sozlesmeli personel", "idari hizmet sozlesmeli personel",
    "sozlesmeli personel", "memur", "personel",
)


def _kurum_key(kurum: str, unvan: str, il: str) -> str:
    k = fold_tr(kurum)
    for suf in _STATU_SUFFIXES:
        if k.endswith(suf):
            k = k[: -len(suf)].strip()
    return f"{k}|{fold_tr(unvan)}|{fold_tr(il)}"


@lru_cache(maxsize=1)
def _taban_index() -> dict[str, list[dict]]:
    """(kurum|unvan|il) fold anahtarı → geçmiş taban kayıtları."""
    _, _, placements = _load()
    idx: dict[str, list[dict]] = {}
    for p in placements:
        key = _kurum_key(p["kurum"], p["unvan"], p.get("il", ""))
        idx.setdefault(key, []).append(p)
    return idx


def _matching_nitelik_codes(bolum: str, duzey: str | None) -> tuple[set[str], set[str]]:
    """Bölüm adına uyan nitelik kodları + jenerik (herkese açık) kodlar."""
    _, nitelikler, _ = _load()
    b = fold_tr(bolum.strip())
    ozel: set[str] = set()
    generic: set[str] = set()
    for kod, n in nitelikler.items():
        if duzey and n["duzey"] != duzey:
            continue
        a = fold_tr(n["aciklama"])
        if b and b in a:
            ozel.add(kod)
        elif any(h in a for h in _GENERIC_HINTS):
            generic.add(kod)
    return ozel, generic


class KpssService:
    def kadro_ara(
        self,
        *,
        bolum: str = "",
        puan: float | None = None,
        duzey: str | None = None,
        il: str | None = None,
        limit: int = 30,
    ) -> dict:
        kadrolar, nitelikler, _ = _load()
        taban_idx = _taban_index()

        ozel, generic = (_matching_nitelik_codes(bolum, duzey)
                         if bolum else (set(), set()))

        items: list[dict] = []
        for k in kadrolar:
            if duzey and k["duzey"] != duzey:
                continue
            if il and fold_tr(k.get("il", "")) != fold_tr(il):
                continue
            kcodes = set(k.get("nitelikler", []))
            if bolum:
                hit_ozel = kcodes & ozel
                hit_gen = kcodes & generic
                if not hit_ozel and not hit_gen:
                    continue
                match_type = "bölüme özel" if hit_ozel else "tüm mezunlara açık"
            else:
                match_type = ""

            # Geçmiş taban (aynı kurum+unvan+il)
            key = _kurum_key(k["kurum"], k["unvan"], k.get("il", ""))
            past = taban_idx.get(key, [])
            son_taban = max(past, key=lambda p: p["donem"])["min_puan"] if past else None

            if puan is not None and son_taban is not None and son_taban > puan + 5:
                continue  # geçmiş taban puanın 5+ üstünde — gerçekçi değil

            items.append({
                "kadro_kodu": k["kadro_kodu"],
                "kurum": k["kurum"],
                "unvan": k["unvan"],
                "il": k.get("il", ""),
                "duzey": k["duzey"],
                "puan_turu": k["puan_turu"],
                "kontenjan": k.get("kontenjan"),
                "eslesme": match_type,
                "gecmis_taban": son_taban,
                "nitelik_aciklama": next(
                    (nitelikler[c]["aciklama"][:160]
                     for c in k.get("nitelikler", []) if c in (ozel or kcodes)
                     and c in nitelikler), ""),
            })

        # Geçmiş tabanı bilinenler önce, taban artan (ulaşılabilirlik)
        items.sort(key=lambda x: (x["gecmis_taban"] is None,
                                  x["gecmis_taban"] or 999))
        return {
            "donem": "2026/1",
            "total": len(items),
            "items": items[:limit],
            "uyari": ("Taban puanlar GEÇMİŞ dönem yerleştirmelerinden (2025) — "
                      "2026/1 tabanları yerleştirme sonrası belli olur."),
        }
