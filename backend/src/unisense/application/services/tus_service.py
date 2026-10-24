"""TUS/DUS uzmanlık tercih servisi — puanına göre yerleşebileceğin programlar.

Aday K/T puanını (+ isteğe bağlı dal/kurum/kontenjan türü) girer → geçen dönem
(ör. 2025-TUS 1. Dönem) en küçük yerleşme puanlarına göre güvenli/tutar/riskli
kovalarında sıralı program (uzmanlık dalı × kurum) listesi döner.

Kural: TUS/DUS'ta YÜKSEK puan = daha iyi. Aday ancak puanı programın en küçük
puanından yüksekse geçen dönem yerleşirdi (p >= taban). Marjlar EK (puan farkı):
  Güvenli: p >= taban + 2   (tabanın belirgin üstünde)
  Tutar:   taban - 1 <= p < taban + 2  (taban civarı, sınırda)
  Riskli:  taban - 4 <= p < taban - 1  (tabanın altında ama taban düşerse şans)

TAHMÎNİDİR: geçen dönem verisine dayanır; kontenjan/başvuru dalgalandığı için bu
dönem taban puanları değişir — garanti değildir. Resmî kaynak: ÖSYM kılavuzu.
Program kodları YÖK Atlas ile eşleşmez (ayrı veri adası).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings

_FOLD = {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"}

# Ek puan marjları (TUS/DUS puanı ~45-80 bandında; birkaç puan anlamlı)
_GUVENLI_MARJ = 2.0   # p - taban >= 2 → güvenli
_TUTAR_ALT = 1.0      # taban - 1 <= p < taban + 2 → tutar
_RISKLI_ALT = 4.0     # taban - 4 <= p < taban - 1 → riskli

_FILES = {"TUS": "tus_rankings.json", "DUS": "dus_rankings.json"}
_META_KEYS = ("sinav", "donem", "guncelleme", "kaynak", "kaynak_url", "toplam", "taban_puanli")

_NOT = (
    "Puanlar geçen dönem ({donem}) ÖSYM en küçük yerleşme puanlarıdır ve "
    "TAHMÎNİDİR — bu dönem taban puanları değişebilir, garanti değildir. "
    "Resmî tercih ve güncel kılavuz için osym.gov.tr."
)


def _fold(s: str) -> str:
    s = (s or "").replace("İ", "i").replace("I", "ı").lower()
    return "".join(_FOLD.get(c, c) for c in s)


@lru_cache(maxsize=2)
def _load(sinav: str) -> dict:
    fname = _FILES.get(sinav)
    if not fname:
        return {"programlar": []}
    p = Path(get_settings().project_root) / "data" / "processed" / fname
    if not p.exists():
        return {"programlar": []}
    return json.load(open(p, encoding="utf-8"))


class TusService:
    def meta(self, sinav: str = "TUS") -> dict:
        d = _load(sinav)
        m = {k: d.get(k) for k in _META_KEYS}
        # Veri dosyası yoksa None'lar şemanın zorunlu str alanlarını patlatır (500)
        m["sinav"] = m.get("sinav") or sinav
        for k in ("donem", "guncelleme", "kaynak", "kaynak_url"):
            m[k] = m.get(k) or ""
        m["dallar"] = sorted({p["dal"] for p in d.get("programlar", []) if p.get("dal")})
        return m

    def oneri(
        self,
        puan: float,
        sinav: str = "TUS",
        dal: str | None = None,
        kontenjan_turu: str | None = None,
        kurum: str | None = None,
        limit: int = 40,
    ) -> dict:
        d = _load(sinav)
        progs = [p for p in d.get("programlar", []) if p.get("min_puan") is not None]
        if dal:
            df = _fold(dal)
            progs = [p for p in progs if _fold(p.get("dal", "")) == df]
        # Varsayılan GENEL: Yabancı Uyruklu kontenjanların tabanları belirgin
        # düşük — filtresiz bırakılırsa TR adayının önerilerine karışıp yanıltır.
        kontenjan_turu = kontenjan_turu or "Genel"
        progs = [p for p in progs if p.get("kontenjan_turu") == kontenjan_turu]
        if kurum:
            kf = _fold(kurum)
            progs = [p for p in progs if kf in _fold(p.get("kurum") or "")]

        guvenli: list[dict] = []
        tutar: list[dict] = []
        riskli: list[dict] = []
        for p in progs:
            diff = puan - p["min_puan"]
            if diff >= _GUVENLI_MARJ:
                guvenli.append(p)
            elif diff >= -_TUTAR_ALT:
                tutar.append(p)
            elif diff >= -_RISKLI_ALT:
                riskli.append(p)

        # Her kovada yüksek taban → düşük (en prestijli/zor program üstte)
        def key(p: dict) -> float:
            return -p["min_puan"]

        meta = {"sinav": d.get("sinav") or sinav, "donem": d.get("donem") or ""}
        return {
            **meta,
            "puan": puan,
            "not": _NOT.format(donem=d.get("donem", "geçen dönem")),
            "sayilar": {"guvenli": len(guvenli), "tutar": len(tutar), "riskli": len(riskli)},
            "guvenli": sorted(guvenli, key=key)[:limit],
            "tutar": sorted(tutar, key=key)[:limit],
            "riskli": sorted(riskli, key=key)[:limit],
        }
