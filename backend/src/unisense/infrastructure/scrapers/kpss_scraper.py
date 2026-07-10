"""KPSS merkezi yerleştirme sonuçları (ÖSYM min/max puanlar) → JSON.

Kaynak: ÖSYM'nin her yerleştirme sonrası yayınladığı "En Küçük ve En Büyük
Puanlar" PDF'leri (dokuman.osym.gov.tr — Referer header'ı ister).
Kadro bazında: kurum, il, unvan, kontenjan, yerleşen ve taban (min) puan.

PDF satır yapısı (tek sütunlu akış):
    302010360                     ← kadro kodu (9 hane)
    AYDIN ADNAN MENDERES ... / AYDIN / MERKEZ
    HEMŞİRE
    5      ← kontenjan
    5      ← yerleşen
    0      ← boş
    76,80831 78,05973             ← min max

Puan türleri (B grubu merkezi yerleştirme): lisans=P3, önlisans=P93,
ortaöğretim=P94.

Çıktı: data/processed/kpss_placements.json
Kullanım: python -m unisense.infrastructure.scrapers.kpss_scraper
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
import requests

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BACKEND = Path(__file__).resolve().parents[4]
OUT = BACKEND / "data" / "processed" / "kpss_placements.json"
CACHE = BACKEND / ".cache" / "kpss"

# ÖSYM duyuru sayfaları — PDF linkleri buradan regex'le bulunur (URL'ler
# dönemden döneme değiştiği için sayfadan çekmek hardcode'dan dayanıklı)
SOURCE_PAGES = {
    "2025/2": "https://www.osym.gov.tr/TR,33774/kpss-20252-bazi-kamu-kurum-ve-kuruluslarin-kadro-ve-pozisyonlarina-yerlestirme-sonuclarina-iliskin-sayisal-bilgiler.html",
    "2025/1": "https://www.osym.gov.tr/TR,33363/kpss-20251-bazi-kamu-kurum-ve-kuruluslarin-kadro-ve-pozisyonlarina-yerlestirme-sonuclarina-iliskin-sayisal-bilgiler.html",
}

# Otomatik keşif: ÖSYM arşiv aramasında yeni "yerleştirme sonuçlarına ilişkin
# sayısal bilgiler" duyuruları taranır — yeni dönem (2026/1, 2026/2...)
# yayınlandığında elle URL eklemeye gerek kalmaz (aylık cron çağırır).
DISCOVER_URL = "https://www.osym.gov.tr/arama?_Dil=1&aranan=kpss+yerlestirme+sonuclarina+iliskin+sayisal"
_DONEM_RE = re.compile(r"kpss-?(20\d\d)(\d)[^0-9]", re.I)


def _discover_pages(s: requests.Session) -> dict[str, str]:
    """ÖSYM arama sayfasından yeni dönem duyurularını keşfet."""
    pages = dict(SOURCE_PAGES)
    try:
        html = s.get(DISCOVER_URL, timeout=60).text
        for m in re.finditer(
            r'href="(/TR,\d+/kpss-?(20\d\d)(\d)-[^"]*sayisal-bilgiler[^"]*\.html)"',
            html, re.I,
        ):
            donem = f"{m.group(2)}/{m.group(3)}"
            pages.setdefault(donem, "https://www.osym.gov.tr" + m.group(1))
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ keşif atlandı ({str(e)[:60]}) — bilinen sayfalarla devam")
    return pages

LEVEL_HINTS = {  # PDF dosya adındaki ipucu → düzey + puan türü
    "lisans": ("lisans", "P3"),
    "onl": ("önlisans", "P93"),
    "ort": ("ortaöğretim", "P94"),
}

_CODE_RE = re.compile(r"^\d{9}$")
# 2025/2 formatı: "76,80831 78,05973" tek satır; 2025/1: her puan ayrı satırda
_SCORES_RE = re.compile(r"^(\d{1,3},\d+)\s+(\d{1,3},\d+)$")
_SINGLE_SCORE_RE = re.compile(r"^(\d{1,3},\d+)$")
_INT_RE = re.compile(r"^\d{1,5}$")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
        "Referer": "https://www.osym.gov.tr/",  # dokuman sunucusu bunsuz boş döner
    })
    return s


def _find_pdfs(s: requests.Session, page_url: str) -> dict[str, str]:
    """Duyuru sayfasından minmax PDF linklerini bul → {düzey_ipucu: url}."""
    html = s.get(page_url, timeout=60).text
    urls = re.findall(r'href="(https://dokuman\.osym\.gov\.tr/[^"]*minmax[^"]*\.pdf)"', html, re.I)
    out = {}
    for u in dict.fromkeys(urls):
        low = u.lower()
        for hint in LEVEL_HINTS:
            if hint in low.rsplit("/", 1)[-1]:
                out[hint] = u
                break
    return out


def _parse_pdf(path: Path, donem: str, duzey: str, puan_turu: str) -> list[dict]:
    doc = fitz.open(path)
    records: list[dict] = []
    cur: dict | None = None
    ints_seen = 0
    scores: list[float] = []

    def _finalize() -> None:
        nonlocal cur, scores
        if cur is None or len(scores) < 2:
            cur, scores = None, []
            return
        cur["min_puan"], cur["max_puan"] = scores[0], scores[1]
        # kurum_raw: "KURUM / İL / İLÇE"
        parts = [p.strip() for p in cur.pop("kurum_raw").split("/")]
        cur["kurum"] = parts[0] if parts else ""
        cur["il"] = parts[1] if len(parts) > 1 else ""
        cur["ilce"] = parts[2] if len(parts) > 2 else ""
        cur.update({"donem": donem, "duzey": duzey, "puan_turu": puan_turu})
        records.append(cur)
        cur, scores = None, []

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line:
                continue
            if _CODE_RE.match(line):
                _finalize()  # önceki kayıt puanlarla bitmişse kapat
                cur = {"kadro_kodu": line, "kurum_raw": "", "unvan": "",
                       "kontenjan": None, "yerlesen": None, "bos": None}
                ints_seen = 0
                scores = []
                continue
            if cur is None:
                continue
            m = _SCORES_RE.match(line)
            if m:
                scores = [float(m.group(1).replace(",", ".")),
                          float(m.group(2).replace(",", "."))]
                _finalize()
                continue
            # Tek satırda tek puan (2025/1 formatı) — sayaçlar dolduysa puandır.
            # DİKKAT: kontenjan/yerleşen/boş tam sayıları da tek başına satır;
            # ondalıklı (virgüllü) olanlar kesin puandır.
            m1 = _SINGLE_SCORE_RE.match(line)
            if m1 and ints_seen >= 3:
                scores.append(float(m1.group(1).replace(",", ".")))
                if len(scores) == 2:
                    _finalize()
                continue
            if _INT_RE.match(line):
                key = ("kontenjan", "yerlesen", "bos")[min(ints_seen, 2)]
                cur[key] = int(line)
                ints_seen += 1
                continue
            # metin satırı sırası: önce kurum/il/ilçe, sonra unvan;
            # daha uzun taşan satırlar unvana eklenir
            if cur["kurum_raw"] and cur["unvan"]:
                cur["unvan"] += " " + line
            elif cur["kurum_raw"]:
                cur["unvan"] = line
            else:
                cur["kurum_raw"] = line
    return records


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    s = _session()
    all_records: list[dict] = []

    pages = _discover_pages(s)
    print(f"📡 {len(pages)} dönem kaynağı (keşif dahil)")
    for donem, page in pages.items():
        pdfs = _find_pdfs(s, page)
        print(f"📄 {donem}: {len(pdfs)} PDF bulundu")
        for hint, url in pdfs.items():
            duzey, puan_turu = LEVEL_HINTS[hint]
            fname = CACHE / f"{donem.replace('/', '_')}_{hint}.pdf"
            if not fname.exists() or fname.stat().st_size < 10_000:
                data = s.get(url, timeout=180).content
                if data[:4] != b"%PDF":
                    print(f"   ⚠️ {duzey}: PDF gelmedi ({len(data)}B) — atlandı")
                    continue
                fname.write_bytes(data)
            recs = _parse_pdf(fname, donem, duzey, puan_turu)
            print(f"   {duzey}: {len(recs)} kadro")
            all_records.extend(recs)

    # Ayıklama: puanı olmayan/eksik kayıtları at
    clean = [r for r in all_records
             if r.get("min_puan") and r.get("kurum") and r.get("unvan")]
    json.dump(clean, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ {len(clean)} kadro kaydı → {OUT}")


if __name__ == "__main__":
    main()
