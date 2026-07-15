"""LGS lise tercih servisi — tersine kişisel öneri.

Öğrenci Türkiye geneli yüzdelik dilimini (+ isteğe bağlı il/ilçe/tür) girer →
geçen yıl (LGS 2025) taban yüzdeliklerine göre güvenli/tutar/riskli kovalarında
sıralı lise listesi döner.

Kural: LGS'de DÜŞÜK yüzdelik = daha iyi/zor okul. Öğrenci ancak kendi yüzdeliği
okulun taban yüzdeliğinden küçük/eşitse yerleşebilir (s <= t).
  Güvenli: s <= t·0.8    (öğrenci taban rankının rahatça içinde)
  Tutar:   t·0.8 < s <= t (sınırda ama içinde)
  Riskli:  t < s <= t·1.25 (tabanın hemen üstünde — belki tutar)

TAHMİNÎDİR: geçen yıl verisine dayanır, bu yılki taban değişebilir. MEB'in resmî
aracı (Rota Maarif) tarama yapar; bu servis onun yapmadığı tersine öneriyi verir.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings

_FOLD = {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"}

# Marj faktörleri (yüzdelik oranı). Düşük yüzdelik = zor okul olduğu için:
_GUVENLI = 0.8   # s <= t·0.8  → rahat
_RISKLI = 1.25   # t < s <= t·1.25 → sınırda

_META_KEYS = ("guncelleme", "kaynak", "not", "yil", "toplam")


def _fold(s: str) -> str:
    s = (s or "").replace("İ", "i").replace("I", "ı").lower()
    return "".join(_FOLD.get(c, c) for c in s)


@lru_cache(maxsize=1)
def _load() -> dict:
    p = Path(get_settings().project_root) / "data" / "processed" / "lgs_liseler.json"
    if not p.exists():
        return {"liseler": []}
    return json.load(open(p, encoding="utf-8"))


def _degerlendir(lise: dict) -> dict:
    """Çok-yıllı arşivden okul değerlendirmesi: taban yüzdeliği yıllar içinde
    küçülüyorsa okul ZORLAŞIYOR (daha iyi yüzdelik gerekir), büyüyorsa
    KOLAYLAŞIYOR. Kopya döner — lru_cache'teki veriyi mutasyona uğratmaz.
    """
    trend = lise.get("trend") or []
    yonu = None
    if len(trend) >= 2:
        sirali = sorted(trend, key=lambda t: t["yil"])
        eski, yeni = sirali[0]["yuzdelik"], sirali[-1]["yuzdelik"]
        if eski and eski > 0:
            oran = yeni / eski
            if oran <= 0.85:
                yonu = "zorlasiyor"      # yüzdelik daraldı → rekabet arttı
            elif oran >= 1.15:
                yonu = "kolaylasiyor"    # yüzdelik genişledi → rekabet azaldı
            else:
                yonu = "istikrarli"
    return {**lise, "trend_yonu": yonu}


class LgsService:
    def meta(self) -> dict:
        d = _load()
        return {k: d.get(k) for k in _META_KEYS}

    def iller(self) -> list[str]:
        """Veride bulunan iller (dropdown için, alfabetik)."""
        d = _load()
        return sorted({x["il"] for x in d.get("liseler", []) if x.get("il")})

    def ilceler(self, il: str) -> list[str]:
        """Seçilen ildeki ilçeler (dropdown için, alfabetik)."""
        ilf = _fold(il)
        d = _load()
        return sorted({
            x["ilce"] for x in d.get("liseler", [])
            if x.get("ilce") and _fold(x.get("il", "")) == ilf
        })

    def oneri(
        self,
        yuzdelik: float,
        il: str | None = None,
        iller: list[str] | None = None,
        ilce: str | None = None,
        turler: list[str] | None = None,
        pansiyon: str | None = None,
        limit: int = 30,
    ) -> dict:
        d = _load()
        liseler = d.get("liseler", [])
        # Çoklu il desteği: `il` (tekil, geriye uyum) + `iller` birleşir
        il_set = {_fold(x) for x in ([il] if il else []) + (iller or []) if x}
        if il_set:
            liseler = [x for x in liseler if _fold(x.get("il", "")) in il_set]
        if ilce:
            icf = _fold(ilce)
            liseler = [x for x in liseler if _fold(x.get("ilce", "")) == icf]
        if turler:
            ts = set(turler)
            liseler = [x for x in liseler if x.get("tur") in ts]
        # Yatılı/yatısız (Rota Maarif'teki pansiyon filtresi):
        # 'var' → pansiyonu olan okullar; 'yok' → pansiyonsuz (gündüz)
        if pansiyon in ("var", "yok"):
            def _pansiyonlu(x: dict) -> bool:
                p = _fold(x.get("pansiyon") or "")
                return bool(p) and p != "yok"
            istenen = pansiyon == "var"
            liseler = [x for x in liseler if _pansiyonlu(x) == istenen]

        guvenli: list[dict] = []
        tutar: list[dict] = []
        riskli: list[dict] = []
        for lise in liseler:
            t = lise.get("yuzdelik")
            if t is None or t <= 0:
                continue
            if yuzdelik <= t * _GUVENLI:
                guvenli.append(_degerlendir(lise))
            elif yuzdelik <= t:
                tutar.append(_degerlendir(lise))
            elif yuzdelik <= t * _RISKLI:
                riskli.append(_degerlendir(lise))

        # Her kovada zor→kolay (küçük yüzdelik önce): en prestijli seçenekler üstte
        def key(lise: dict) -> float:
            return lise["yuzdelik"]
        return {
            "yuzdelik": yuzdelik,
            **self.meta(),
            "sayilar": {"guvenli": len(guvenli), "tutar": len(tutar), "riskli": len(riskli)},
            "guvenli": sorted(guvenli, key=key)[:limit],
            "tutar": sorted(tutar, key=key)[:limit],
            "riskli": sorted(riskli, key=key)[:limit],
        }
