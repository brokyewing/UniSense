"""TUS/DUS yerleştirme sonuçları (ÖSYM en küçük/en büyük puan) → tus_rankings.json,
dus_rankings.json.

Kaynak: ÖSYM'nin her dönem yayınladığı "Yerleştirme Sonuçlarına İlişkin Sayısal
Bilgiler" sayfasındaki min/max PDF'i (DGS ile aynı ÖSYM şablonu).

PDF satır düzeni (tek akış, get_text):
    707600101                          ← program kodu (9 hane)
    Adli Tıp Kurumu/ADLİ TIP           ← ad = "Kurum/DAL" (çok satırlı olabilir)
    Genel                              ← kontenjan türü (Genel | Yabancı Uyruklu)
    10                                 ← kontenjan
    10                                 ← yerleşen
    0                                  ← boş
    58,49505 64,78943                  ← en küçük + en büyük (yerleşen 0 ise "--")

NOT: Program kodları YÖK Atlas lisans kodlarıyla EŞLEŞMEZ (DGS'nin aksine) →
ayrı bir veri adasıdır, departments/rankings ile birleşmez.

URL deseni dönemler arası tutarsız (TERCIH vs YERLESTIRME klasörü) → sabit PDF
URL'i tahmin edilemez; her dönem 'Sayısal Bilgiler' HTML sayfasından link scrape
edilir. Bilinen son dönem sayfaları aşağıda; ÖSYM arama ile daha yenisi bulunursa
o kullanılır.

Çıktı: data/processed/tus_rankings.json, dus_rankings.json
Kullanım: python -m unisense.infrastructure.scrapers.tusdus_scraper
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import fitz
import requests

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BACKEND = Path(__file__).resolve().parents[4]
CACHE = BACKEND / ".cache" / "tusdus"

# Sınav başına: bilinen son 'Sayısal Bilgiler' sayfası + ÖSYM arama sorgusu.
# Keşif daha yeni dönem bulursa onu kullanır; bulamazsa bilinen sayfa.
CONFIG = {
    "TUS": {
        "out": BACKEND / "data" / "processed" / "tus_rankings.json",
        "donem": "2025 1. Dönem",
        "min_kayit": 1500,  # bunun altı = PDF formatı değişmiş/bozuk → YAZMA
        "known_page": ("https://www.osym.gov.tr/TR,33253/"
                       "2025-tus-1-donem-yerlestirme-sonuclarina-iliskin-sayisal-bilgiler.html"),
        "search": ("https://www.osym.gov.tr/arama?_Dil=1&aranan="
                   "tus+yerlestirme+sonuclarina+iliskin+sayisal"),
        "page_re": r'href="(/TR,\d+/(20\d\d)-tus-(\d)-donem-yerlestirme-sonuclarina[^"]*\.html)"',
    },
    "DUS": {
        "out": BACKEND / "data" / "processed" / "dus_rankings.json",
        "donem": "2025 2. Dönem",
        "min_kayit": 200,
        "known_page": ("https://www.osym.gov.tr/TR,33701/"
                       "2025-dus-2-donem-yerlestirme-sonuclarina-iliskin-sayisal-bilgiler.html"),
        "search": ("https://www.osym.gov.tr/arama?_Dil=1&aranan="
                   "dus+yerlestirme+sonuclarina+iliskin+sayisal"),
        "page_re": r'href="(/TR,\d+/(20\d\d)-dus-(\d)-donem-yerlestirme-sonuclarina[^"]*\.html)"',
    },
}

_CODE_RE = re.compile(r"^\d{9}$")
_INT_RE = re.compile(r"^\d{1,4}$")
_SCORE_RE = re.compile(r"\d{1,3},\d+")
# Başlık satırları (her sayfada tekrar eder) — parse'a girmez
_HEADER_TOKENS = {
    "Program Kodu", "Program Adı", "Kontenjan", "Türü", "Sayısı",
    "Yerleşen Aday", "Boş Kalan Kontenjan", "En Küçük", "En Büyük", "Puan",
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
        "Referer": "https://www.osym.gov.tr/",
    })
    return s


def _discover(s: requests.Session, cfg: dict) -> tuple[str, str]:
    """(donem_etiketi, sayfa_url) — arama daha yeni dönem bulursa onu döndür."""
    try:
        html = s.get(cfg["search"], timeout=60).text
        best = None  # (yil, donem, url)
        for m in re.finditer(cfg["page_re"], html, re.I):
            yil, donem = int(m.group(2)), int(m.group(3))
            key = (yil, donem)
            if best is None or key > best[0]:
                best = (key, "https://www.osym.gov.tr" + m.group(1))
        if best:
            (yil, donem), url = best
            return f"{yil} {donem}. Dönem", url
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ keşif atlandı ({str(e)[:60]})")
    return cfg["donem"], cfg["known_page"]


def _parse(path: Path) -> list[dict]:
    doc = fitz.open(path)
    records: list[dict] = []
    cur: dict | None = None
    buf: list[str] = []       # ad + tür metin satırları
    ints: list[int] = []
    scores: list[float] = []

    def flush() -> None:
        nonlocal cur, buf, ints, scores
        if cur and len(ints) >= 3 and buf:
            tur = buf[-1]
            ad = " ".join(buf[:-1]).strip()
            kurum, _, dal = ad.rpartition("/")
            cur.update({
                "ad": ad,
                "kurum": kurum.strip() or None,
                "dal": dal.strip() or ad,
                "kontenjan_turu": tur,
                "kontenjan": ints[0],
                "yerlesen": ints[1],
                "bos": ints[2],
                "min_puan": round(scores[0], 3) if scores else None,
                "max_puan": round(scores[1], 3) if len(scores) > 1
                else (round(scores[0], 3) if scores else None),
            })
            records.append(cur)
        cur, buf, ints, scores = None, [], [], []

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line or line in _HEADER_TOKENS:
                continue
            if _CODE_RE.match(line):
                flush()
                cur = {"kod": line}
                continue
            if cur is None:
                continue
            if _INT_RE.match(line) and buf:  # sayısal blok başladı (ad bitti)
                ints.append(int(line))
                continue
            found = _SCORE_RE.findall(line)
            if found:
                scores.extend(float(x.replace(",", ".")) for x in found)
                continue
            if line == "--":
                continue
            if not ints:  # henüz sayısal bloğa girmedik → ad/tür metni
                buf.append(line)
    flush()
    return records


def _scrape_one(s: requests.Session, sinav: str, cfg: dict) -> None:
    donem, page_url = _discover(s, cfg)
    print(f"📡 {sinav} {donem} → {page_url[:80]}")
    html = s.get(page_url, timeout=60).text
    pdfs = re.findall(
        r'href="(https://dokuman\.osym\.gov\.tr/[^"]*minmax[^"]*\.pdf)"', html, re.I)
    if not pdfs:
        print(f"   ⛔ {sinav} min/max PDF bulunamadı — atlandı")
        return
    p = CACHE / f"{sinav.lower()}_minmax.pdf"
    if not p.exists() or p.stat().st_size < 10_000:
        data = s.get(pdfs[0], timeout=180).content
        if data[:4] != b"%PDF":
            print(f"   ⛔ {sinav} PDF gelmedi — atlandı")
            return
        p.write_bytes(data)

    programlar = _parse(p)
    # Güvenlik tabanı: gözetimsiz cron main'e push ettiği için, PDF formatı
    # değişip parse çökerse bozuk/eksik veriyi ÜZERİNE YAZMA — eski veri kalsın.
    floor = cfg.get("min_kayit", 0)
    if len(programlar) < floor:
        print(f"   ⛔ {sinav}: yalnız {len(programlar)} kayıt (<{floor}) — PDF formatı "
              f"değişmiş olabilir; {cfg['out'].name} GÜNCELLENMEDİ (eski veri korundu)")
        return
    dolu = sum(1 for r in programlar if r.get("min_puan") is not None)
    out = {
        "sinav": sinav,
        "donem": donem,
        "guncelleme": donem.split()[0],
        "kaynak": f"ÖSYM {donem} {sinav} Yerleştirme Sayısal Bilgiler",
        "kaynak_url": page_url,
        "toplam": len(programlar),
        "taban_puanli": dolu,
        "programlar": programlar,
    }
    cfg["out"].parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(cfg["out"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"   ✅ {len(programlar)} program ({dolu} taban puanlı) → {cfg['out'].name}")


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    s = _session()
    for sinav, cfg in CONFIG.items():
        try:
            _scrape_one(s, sinav, cfg)
        except Exception as e:  # noqa: BLE001
            print(f"   ⛔ {sinav} hata: {str(e)[:80]}")


if __name__ == "__main__":
    main()
