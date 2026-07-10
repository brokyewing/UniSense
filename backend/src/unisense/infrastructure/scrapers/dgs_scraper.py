"""DGS yerleştirme sonuçları (ÖSYM min/max) → dgs_rankings.json.

Kaynak: ÖSYM'nin yıllık "DGS Yerleştirme Sonuçlarına İlişkin En Küçük ve
En Büyük Puanlar" PDF'i. Program kodları YÖK Atlas lisans kodlarıyla AYNI
olduğu için mevcut departments/rankings verisiyle doğrudan birleşir.

PDF satır düzeni (tek akış):
    100290165                                   ← program kodu
    ADIYAMAN ÜNİVERSİTESİ/Sağlık.../Ebelik ...  ← ad (1+ satır)
    SAY                                         ← DGS puan türü
    1 / 0 / 1                                   ← kontenjan, yerleşen, boş
    282,64512  (yerleşen 0 ise puan satırı yok)
    ...

Çıktı: data/processed/dgs_rankings.json
Kullanım: python -m unisense.infrastructure.scrapers.dgs_scraper
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import requests

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BACKEND = Path(__file__).resolve().parents[4]
OUT = BACKEND / "data" / "processed" / "dgs_rankings.json"
CACHE = BACKEND / ".cache" / "dgs"

# Bilinen son yayın; keşif daha yenisini bulursa onu kullanır
KNOWN_YEAR = 2025
KNOWN_PAGE = ("https://www.osym.gov.tr/TR,33469/"
              "2025-dgs-yerlestirme-sonuclarina-iliskin-sayisal-bilgiler.html")
DISCOVER_URL = ("https://www.osym.gov.tr/arama?_Dil=1&aranan="
                "dgs+yerlestirme+sonuclarina+iliskin+sayisal")

_CODE_RE = re.compile(r"^\d{9}$")
_PTYPE_RE = re.compile(r"^(SAY|EA|SÖZ|SOZ)$")
_INT_RE = re.compile(r"^\d{1,4}$")
_SCORE_RE = re.compile(r"^\d{1,3},\d+$")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
        "Referer": "https://www.osym.gov.tr/",
    })
    return s


def _discover(s: requests.Session) -> tuple[int, str]:
    try:
        html = s.get(DISCOVER_URL, timeout=60).text
        best = None
        for m in re.finditer(
            r'href="(/TR,\d+/(20\d\d)-dgs-yerlestirme-sonuclarina[^"]*\.html)"',
            html, re.I,
        ):
            year = int(m.group(2))
            if best is None or year > best[0]:
                best = (year, "https://www.osym.gov.tr" + m.group(1))
        if best and best[0] > KNOWN_YEAR:
            return best
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ keşif atlandı ({str(e)[:60]})")
    return KNOWN_YEAR, KNOWN_PAGE


def _parse(path: Path, year: int) -> list[dict]:
    doc = fitz.open(path)
    records: list[dict] = []
    cur: dict | None = None
    ints: list[int] = []
    scores: list[float] = []
    name_buf: list[str] = []

    def _flush() -> None:
        nonlocal cur, ints, scores, name_buf
        if cur and len(ints) >= 3:
            cur["program_adi"] = " ".join(name_buf).strip()
            cur["kontenjan"], cur["yerlesen"], cur["bos"] = ints[0], ints[1], ints[2]
            cur["min_puan"] = scores[0] if scores else None
            cur["max_puan"] = scores[1] if len(scores) > 1 else None
            cur["yil"] = year
            records.append(cur)
        cur, ints, scores, name_buf = None, [], [], []

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line:
                continue
            if _CODE_RE.match(line):
                _flush()
                cur = {"department_code": line}
                continue
            if cur is None:
                continue
            if _PTYPE_RE.match(line):
                cur["puan_turu"] = "SÖZ" if line == "SOZ" else line
                continue
            if _SCORE_RE.match(line):
                scores.append(float(line.replace(",", ".")))
                continue
            if _INT_RE.match(line) and "puan_turu" in cur:
                ints.append(int(line))
                continue
            if "puan_turu" not in cur:
                name_buf.append(line)
    _flush()
    return records


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    s = _session()

    year, page_url = _discover(s)
    print(f"📡 DGS {year} → {page_url[:80]}")
    html = s.get(page_url, timeout=60).text
    pdfs = re.findall(
        r'href="(https://dokuman\.osym\.gov\.tr/[^"]*minmax[^"]*\.pdf)"', html, re.I)
    if not pdfs:
        print("⛔ min/max PDF bulunamadı")
        return
    p = CACHE / f"minmax_{year}.pdf"
    if not p.exists() or p.stat().st_size < 10_000:
        data = s.get(pdfs[0], timeout=180).content
        if data[:4] != b"%PDF":
            raise RuntimeError("PDF gelmedi")
        p.write_bytes(data)

    records = _parse(p, year)
    dolu = sum(1 for r in records if r.get("min_puan"))
    json.dump(records, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ {len(records)} DGS kaydı ({dolu} taban puanlı) → {OUT}")


if __name__ == "__main__":
    main()
