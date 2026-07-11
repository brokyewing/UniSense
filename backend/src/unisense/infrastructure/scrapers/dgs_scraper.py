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

import bisect
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


_T2_Y_TOP, _T2_Y_FOOT = 128.0, 740.0


def _parse_tablo2(path: Path) -> list[dict]:
    """Önlisans alanı → geçilebilecek lisans programları.

    Yapı (BULGU #3): her GRUP = solda bir önlisans program ailesi + sağda
    hepsinin geçebileceği ortak lisans programları (iki bağımsız-uzunlukta
    paralel liste). Grup sınırı = tablodaki YATAY AYRAÇ ÇİZGİLERİ (get_drawings).
    Önceki parser 9xxx kodlu önlisans girdilerini 'grup başlığı' sanıp yanlış
    bölüyor, lisans hedeflerini karıştırıyordu (adalet→Grafik+Hukuk gibi).
    Kolonlar: kod x<45 | önlisans adı 45–260 | lisans adı 260–500 |
              lisans kodu 500–555 | puan türü ≥555.
    """
    doc = fitz.open(path)
    onl: list[dict] = []   # {gy, code, name}
    lis: list[dict] = []   # {gy, name, lkod, pt}
    seps: list[float] = []  # grup ayraç çizgilerinin global-y'si

    for pno, page in enumerate(doc):
        base = pno * 1000.0
        words = [w for w in page.get_text("words")
                 if _T2_Y_TOP <= w[1] <= _T2_Y_FOOT]
        # Grup ayraç çizgileri (başlık altındaki geniş yatay çizgiler)
        for d in page.get_drawings():
            for it in d.get("items", []):
                if (it[0] == "l" and abs(it[1].y - it[2].y) < 1.0
                        and abs(it[1].x - it[2].x) > 150
                        and _T2_Y_TOP <= it[1].y <= _T2_Y_FOOT):
                    seps.append(base + round(it[1].y, 1))
        # Önlisans (sol): 4-haneli kod çapa, isim eklenir (çok satırlı olabilir)
        cur: dict | None = None
        for w in sorted((w for w in words if w[0] < 260), key=lambda w: (w[1], w[0])):
            x0, y0, txt = w[0], w[1], w[4]
            if x0 < 45 and re.fullmatch(r"\d{4}", txt):
                cur = {"gy": base + y0, "code": txt, "name": ""}
                onl.append(cur)
            elif 45 <= x0 < 260 and cur is not None:
                cur["name"] = f"{cur['name']} {txt}".strip()
        # Lisans (sağ): lkod çapa, isim y-bandı, puan türü aynı satırda
        lkods = sorted(((w[1], w[4]) for w in words
                        if 500 <= w[0] < 555 and re.fullmatch(r"\d{4}", w[4])),
                       key=lambda t: t[0])
        names = sorted(((w[1], w[0], w[4]) for w in words if 260 <= w[0] < 500),
                       key=lambda t: (t[0], t[1]))
        pts = [(w[1], w[4]) for w in words if w[0] >= 555 and w[4] in _PT_SET]
        for i, (ly, lkod) in enumerate(lkods):
            lo = ly - 6.0
            hi = lkods[i + 1][0] - 6.0 if i + 1 < len(lkods) else 1e9
            nm = " ".join(t[2] for t in names if lo <= t[0] < hi).strip()
            nm = re.sub(r"\s*\d{1,2}$", "", nm).strip()  # sızan sayfa no'yu at
            pt = next((p for py, p in pts if abs(py - ly) < 6.0), "")
            if nm:
                lis.append({"gy": base + ly, "name": nm, "lkod": lkod, "pt": pt})

    seps = sorted(set(seps))

    def _grp(gy: float) -> int:
        return bisect.bisect_right(seps, gy)

    groups: dict[int, dict] = {}
    for entry in sorted(lis, key=lambda e: e["gy"]):
        g = groups.setdefault(_grp(entry["gy"]),
                              {"onlisans_kod": "", "onlisans_adi": "",
                               "programlar": [], "lisans": []})
        g["lisans"].append({"ad": entry["name"], "kod": entry["lkod"],
                            "puan_turu": entry["pt"]})
    for o in sorted(onl, key=lambda e: e["gy"]):
        if not o["name"]:
            continue
        g = groups.setdefault(_grp(o["gy"]),
                              {"onlisans_kod": "", "onlisans_adi": "",
                               "programlar": [], "lisans": []})
        g["programlar"].append({"kod": o["code"], "ad": o["name"]})

    out: list[dict] = []
    for _, g in sorted(groups.items()):
        if not (g["lisans"] and g["programlar"]):
            continue
        # Temsili grup adı = ilk önlisans programı (arama sonucunda etiket olur)
        g["onlisans_adi"] = g["programlar"][0]["ad"]
        g["onlisans_kod"] = g["programlar"][0]["kod"]
        out.append(g)
    return out


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
