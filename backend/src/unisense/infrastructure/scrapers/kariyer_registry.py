"""Kaynak kayıt defteri yükleyici (yol haritası F0.4).

Defter: backend/data/kaynaklar/is_kaynaklari.yml — kod değil veri.
Zorunlu alanlar: kod, ad, hat, url, erisim, aktif.
erisim ∈ {api, rss, sitemap, html, toleransli, yok}.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ZORUNLU = ("kod", "ad", "hat", "url", "erisim")
ERISIMLER = ("api", "rss", "sitemap", "html", "toleransli", "yok")

VARSAYILAN_DEFTER = (
    Path(__file__).resolve().parents[4] / "data" / "kaynaklar" / "is_kaynaklari.yml"
)


def defter_yolu() -> Path:
    return VARSAYILAN_DEFTER


def yukle(yol: Path | str | None = None) -> list[dict]:
    """Defteri okur + doğrular. Dosya yoksa/kırık ise hata fırlatır
    (sessiz başarı yasak — çağıran exit 1 ile düşer)."""
    p = Path(yol) if yol else defter_yolu()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("kaynaklar"), list):
        raise ValueError(f"{p}: 'kaynaklar' listesi bulunamadı")
    girdiler: list[dict] = []
    gorulen: set[str] = set()
    for i, g in enumerate(data["kaynaklar"]):
        if not isinstance(g, dict):
            raise ValueError(f"{p}: girdi #{i} sözlük değil")
        eksik = [a for a in ZORUNLU if a not in g]
        if eksik:
            raise ValueError(f"{p}: '{g.get('kod', i)}' eksik alan: {eksik}")
        if g["erisim"] not in ERISIMLER:
            raise ValueError(f"{p}: '{g['kod']}' geçersiz erisim: {g['erisim']}")
        if g["kod"] in gorulen:
            raise ValueError(f"{p}: yinelenen kod: {g['kod']}")
        gorulen.add(g["kod"])
        g.setdefault("aktif", True)
        g.setdefault("params", {})
        girdiler.append(g)
    return girdiler


def aktifler(yol: Path | str | None = None) -> list[dict]:
    return [g for g in yukle(yol) if g.get("aktif")]


def sirket_ats(yol: Path | str | None = None) -> list[dict]:
    """Şirket → ATS eşlemesi (F4.2). Doğrulamasız geçirir (adaptör kullanırken
    API'yi kendisi dener); kayıt defteri şeması değişirse burası güncellenir."""
    p = Path(yol) if yol else defter_yolu()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{p}: sözlük değil")
    liste = data.get("sirket_ats") or []
    if not isinstance(liste, list):
        raise ValueError(f"{p}: 'sirket_ats' liste değil")
    return liste
