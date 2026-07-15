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


@lru_cache(maxsize=1)
def _load_ek() -> tuple[dict, dict]:
    """Mezuniyet alanları (kod→ad) + özel koşullar (kod→metin)."""
    proc = Path(get_settings().project_root) / "data" / "processed"

    def _j(name):
        p = proc / name
        return json.load(open(p, encoding="utf-8")) if p.exists() else {}

    return _j("kpss_mezuniyet_alanlari.json"), _j("kpss_ozel_kosullar.json")


def _bolum_alan_kodlari(bolum: str, duzey: str | None) -> set[str]:
    """Bölüm adı → resmi mezuniyet alan kodları (kod-bazlı eşleşme anahtarı)."""
    alanlar, _ = _load_ek()
    b = fold_tr(bolum.strip())
    if not b:
        return set()
    return {kod for kod, a in alanlar.items()
            if (not duzey or a["duzey"] == duzey) and b in fold_tr(a["ad"])}


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


def _matching_nitelik_codes(bolum: str, duzey: str | None) -> tuple[set[str], set[str], set[str]]:
    """Bölüme uyan nitelikler: (kod-bazlı KESİN, ad-bazlı, jenerik).

    Kod-bazlı: bölümün resmi mezuniyet alan kodu, niteliğin alan_kodlari
    listesinde geçiyorsa — ÖSYM'nin kendi eşleşmesi, yanlış pozitif üretmez.
    Ad-bazlı: açıklama metninde bölüm adı geçenler (kodsuz nitelikler için yedek).
    """
    _, nitelikler, _ = _load()
    b = fold_tr(bolum.strip())
    alan_kodlari = _bolum_alan_kodlari(bolum, duzey)
    kesin: set[str] = set()
    adli: set[str] = set()
    generic: set[str] = set()
    for kod, n in nitelikler.items():
        if duzey and n["duzey"] != duzey:
            continue
        if alan_kodlari and alan_kodlari & set(n.get("alan_kodlari") or []):
            kesin.add(kod)
            continue
        a = fold_tr(n["aciklama"])
        if b and b in a:
            adli.add(kod)
        elif any(h in a for h in _GENERIC_HINTS):
            generic.add(kod)
    return kesin, adli, generic


class KpssService:
    def kadro_ara(
        self,
        *,
        bolum: str = "",
        puan: float | None = None,
        duzey: str | None = None,
        il: str | None = None,
        iller: list[str] | None = None,
        limit: int = 30,
    ) -> dict:
        kadrolar, nitelikler, _ = _load()
        _, kosullar = _load_ek()
        taban_idx = _taban_index()

        kesin, adli, generic = (_matching_nitelik_codes(bolum, duzey)
                                if bolum else (set(), set(), set()))

        # Çoklu il desteği: `il` (tekil, geriye uyum) + `iller` birleşir
        il_set = {fold_tr(x) for x in ([il] if il else []) + (iller or []) if x}

        items: list[dict] = []
        for k in kadrolar:
            if duzey and k["duzey"] != duzey:
                continue
            if il_set and fold_tr(k.get("il", "")) not in il_set:
                continue
            kcodes = set(k.get("nitelikler", []))
            if bolum:
                if kcodes & kesin:
                    match_type = "bölüme özel ✓"      # ÖSYM kod eşleşmesi
                elif kcodes & adli:
                    match_type = "bölüme özel"
                elif kcodes & generic:
                    match_type = "tüm mezunlara açık"
                else:
                    continue
            else:
                match_type = ""

            # Özel koşullar (yaş/YDS/sertifika...) — kullanıcı bilmeden
            # başvurup elenmesin
            ozel_kosullar = [kosullar[c] for c in kcodes if c in kosullar]

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
                "ozel_kosullar": ozel_kosullar[:3],
                "nitelik_aciklama": next(
                    (nitelikler[c]["aciklama"][:160]
                     for c in k.get("nitelikler", [])
                     if c in ((kesin | adli) or kcodes) and c in nitelikler), ""),
            })

        # Geçmiş tabanı bilinenler önce, taban artan (ulaşılabilirlik)
        items.sort(key=lambda x: (x["gecmis_taban"] is None,
                                  x["gecmis_taban"] or 999))
        return {
            "donem": "2026/1",
            "total": len(items),
            "toplam_kontenjan": sum((it.get("kontenjan") or 0) for it in items),
            "items": items[:limit],
            "uyari": ("Taban puanlar GEÇMİŞ dönem yerleştirmelerinden (2025) — "
                      "2026/1 tabanları yerleştirme sonrası belli olur."),
        }

    def donem_ozeti(self) -> dict:
        """Aktif dönemin genel istatistiği: toplam kadro + kontenjan, düzey kırılımı.

        'Toplam kaç kontenjan / kaç kişilik açıldı' gibi istatistik soruları
        için — tekil kadro örnekleri değil, bütünün özeti gerekir (BULGU).
        """
        kadrolar, _, _ = _load()
        donem = kadrolar[0].get("donem", "2026/1") if kadrolar else "2026/1"
        duzeyler: dict[str, dict] = {}
        for k in kadrolar:
            d = duzeyler.setdefault(k.get("duzey", "?"), {"kadro": 0, "kontenjan": 0})
            d["kadro"] += 1
            d["kontenjan"] += k.get("kontenjan") or 0
        return {
            "donem": donem,
            "toplam_kadro": len(kadrolar),
            "toplam_kontenjan": sum((k.get("kontenjan") or 0) for k in kadrolar),
            "kurum_sayisi": len({k.get("kurum", "") for k in kadrolar}),
            "il_sayisi": len({k.get("il", "") for k in kadrolar if k.get("il")}),
            "duzeyler": duzeyler,
        }
