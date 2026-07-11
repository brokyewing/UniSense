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


# === Tablo-2: Önlisans mezuniyet alanı → geçilebilecek lisans programları ===
OUT_GECIS = BACKEND / "data" / "processed" / "dgs_gecis.json"
TABLO2_KNOWN = ("https://dokuman.osym.gov.tr/pdfdokuman/2025/DGS/TERCIH/"
                "tablo2_dgtd28082025.pdf")
_PT_SET = {"SAY", "EA", "SÖZ", "DİL"}


def _parse_tablo2(path: Path) -> list[dict]:
    """Önlisans alanı → geçilebilecek lisans programları (KOORDİNAT bazlı).

    Tablo iki sütunlu; düz metin akışı sütunları karıştırır. x konumları:
      ~26 alan kodu | ~53 alan adı | ~286 lisans adı | ~526 kod | ~566 puan türü
    """
    doc = fitz.open(path)
    gruplar: list[dict] = []
    cur: dict | None = None          # aktif alan GRUBU (9xxx başlık)
    pending_name: str | None = None  # sağ sütun lisans adı
    pending_code: str | None = None
    member_open = False              # sol sütunda üye programı adı bekleniyor

    def _flush() -> None:
        nonlocal cur
        if cur and cur["lisans"]:
            gruplar.append(cur)
        cur = None

    for page in doc:
        # Satırları y-sırasına koy (blok sırası sütun karıştırabiliyor)
        rows: list[tuple[float, float, str]] = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                txt = " ".join(s["text"] for s in line["spans"]).strip()
                if txt:
                    rows.append((line["bbox"][1], line["bbox"][0], txt))
        rows.sort()

        for _y, x0, txt in rows:
            if x0 < 45 and re.match(r"^\d{4}$", txt):
                if txt.startswith("9"):
                    # Yeni alan GRUBU başlığı
                    _flush()
                    cur = {"onlisans_kod": txt, "onlisans_adi": "",
                           "programlar": [], "lisans": []}
                    member_open = False
                elif cur is not None:
                    # Grubun üye önlisans programı (kendi koduyla)
                    cur["programlar"].append({"kod": txt, "ad": ""})
                    member_open = True
            elif 45 <= x0 < 260 and cur is not None:
                if member_open and cur["programlar"]:
                    m = cur["programlar"][-1]
                    m["ad"] = f"{m['ad']} {txt}".strip()
                elif not cur["programlar"]:
                    cur["onlisans_adi"] = f"{cur['onlisans_adi']} {txt}".strip()
                else:
                    # kodsuz devam satırı — son üyeye ekle
                    m = cur["programlar"][-1]
                    m["ad"] = f"{m['ad']} {txt}".strip()
            elif 260 <= x0 < 500 and cur is not None:
                pending_name = f"{pending_name} {txt}".strip() if pending_name else txt
            elif 500 <= x0 < 555 and re.match(r"^\d{4}$", txt):
                pending_code = txt
            elif x0 >= 555 and txt in _PT_SET and cur is not None:
                if pending_name and pending_code:
                    cur["lisans"].append({"ad": pending_name, "kod": pending_code,
                                          "puan_turu": txt})
                pending_name = pending_code = None
    _flush()
    return gruplar


def scrape_tablo2(s: requests.Session) -> None:
    p = CACHE / "tablo2_2025.pdf"
    if not p.exists() or p.stat().st_size < 10_000:
        data = s.get(TABLO2_KNOWN, timeout=180).content
        if data[:4] != b"%PDF":
            print("⛔ Tablo-2 PDF gelmedi — geçiş eşleşmesi atlandı")
            return
        p.write_bytes(data)
    alanlar = _parse_tablo2(p)
    n_lisans = sum(len(a["lisans"]) for a in alanlar)
    json.dump(alanlar, open(OUT_GECIS, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(alanlar)} önlisans alanı → {n_lisans} lisans eşleşmesi → {OUT_GECIS}")


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    s = _session()

    scrape_tablo2(s)

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
