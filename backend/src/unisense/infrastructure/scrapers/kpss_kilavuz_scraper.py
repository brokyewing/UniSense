"""KPSS-2026/1 tercih kılavuzu tabloları → kadrolar + nitelik sözlüğü.

Aktif tercih dönemi verisi (min/max scraper'daki GEÇMİŞ yerleştirmelerin
aksine): şu an başvurulabilen kadrolar + hangi bölüm mezununun hangi
kadroya başvurabileceğini belirleyen NİTELİK KODLARI.

Çıktılar:
  data/processed/kpss_kadrolar.json    — aktif dönem kadroları
  data/processed/kpss_nitelikler.json  — nitelik kodu → öğrenim açıklaması

Kullanım: python -m unisense.infrastructure.scrapers.kpss_kilavuz_scraper
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
OUT_KADRO = BACKEND / "data" / "processed" / "kpss_kadrolar.json"
OUT_NITELIK = BACKEND / "data" / "processed" / "kpss_nitelikler.json"
OUT_ALANLAR = BACKEND / "data" / "processed" / "kpss_mezuniyet_alanlari.json"
OUT_KOSULLAR = BACKEND / "data" / "processed" / "kpss_ozel_kosullar.json"
CACHE = BACKEND / ".cache" / "kpss"

# Varsayılan (bilinen son dönem) — keşif başarısızsa buna düşülür
DONEM = "2026/1"
KILAVUZ_PAGE = ("https://www.osym.gov.tr/TR,34174/kpss-20261-bazi-kamu-kurum-ve-"
                "kuruluslarinin-kadro-ve-pozisyonlarina-yerlestirme-yapmak-icin-"
                "tercih-kilavuzu-ve-tablolar.html")
# Yeni dönem kılavuzu otomatik keşfi (aylık cron için)
DISCOVER_URL = ("https://www.osym.gov.tr/arama?_Dil=1&aranan="
                "kpss+tercih+kilavuzu+ve+tablolar")


def _discover_kilavuz(s: requests.Session) -> tuple[str, str]:
    """En yeni KPSS tercih kılavuzu duyurusunu bul → (dönem, sayfa_url)."""
    known = tuple(int(x) for x in DONEM.split("/"))
    try:
        html = s.get(DISCOVER_URL, timeout=60).text
        best = None
        for m in re.finditer(
            r'href="(/TR,\d+/kpss-?(20\d\d)(\d)-[^"]*tercih-kilavuzu[^"]*\.html)"',
            html, re.I,
        ):
            key = (int(m.group(2)), int(m.group(3)))  # (yıl, dönem) — en yenisi
            if best is None or key > best[0]:
                best = (key, f"{m.group(2)}/{m.group(3)}",
                        "https://www.osym.gov.tr" + m.group(1))
        # Keşfedilen, bilinen dönemden YENİYSE kullan; eskiyse bilinene düş
        if best and best[0] > known:
            return best[1], best[2]
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ kılavuz keşfi atlandı ({str(e)[:60]})")
    return DONEM, KILAVUZ_PAGE


def _find_kilavuz_pdfs(s: requests.Session, page_url: str) -> tuple[dict, dict]:
    """Kılavuz sayfasından tablo + nitelik PDF linklerini çıkar."""
    html = s.get(page_url, timeout=60).text
    urls = re.findall(r'href="(https://dokuman\.osym\.gov\.tr/[^"]*\.pdf)"', html, re.I)
    tablolar, nitelikler, ekler = {}, {}, {}
    for u in dict.fromkeys(urls):
        fname = u.rsplit("/", 1)[-1].lower()
        m = re.match(r"tablo(\d)_", fname)
        if m:
            tablolar[f"tablo{m.group(1)}"] = u
        elif "lisans-nitelik" in fname and "onlisans" not in fname:
            nitelikler["lisans"] = u
        elif "onlisans-nitelik" in fname:
            nitelikler["önlisans"] = u
        elif "ortaogretim-nitelik" in fname:
            nitelikler["ortaöğretim"] = u
        elif "mezunolunan-lisans" in fname:
            ekler["mezun_lisans"] = u
        elif "onlisansprg" in fname:
            ekler["mezun_önlisans"] = u
        elif "alandal" in fname:
            ekler["mezun_ortaöğretim"] = u
        elif "ozelkosullar" in fname:
            ekler["ozelkosullar"] = u
    return tablolar, nitelikler, ekler

# Kadro kodu ilk hanesi → düzey + merkezi yerleştirme puan türü
_LEVEL_BY_PREFIX = {"1": ("ortaöğretim", "P94"), "2": ("önlisans", "P93"),
                    "3": ("lisans", "P3")}

_KADRO_RE = re.compile(r"^\d{9}$")
_KURUMKODU_RE = re.compile(r"^\d{5}$")
_NITELIK_LINE_RE = re.compile(r"^(\d{4})(\s+\d{4})*$")
_KONTENJAN_RE = re.compile(r"^\d{1,4}$")
_TESKILAT = {"MERKEZ", "TAŞRA", "YURTDIŞI", "TAŞRA TEŞKİLATI", "DÖNER SERMAYE"}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
        "Referer": "https://www.osym.gov.tr/",
    })
    return s


def _get(s: requests.Session, url: str, name: str) -> Path:
    p = CACHE / name
    if not p.exists() or p.stat().st_size < 10_000:
        data = s.get(url, timeout=180).content
        if data[:4] != b"%PDF":
            raise RuntimeError(f"PDF gelmedi: {url} ({len(data)}B)")
        p.write_bytes(data)
    return p


def _parse_tablo(path: Path) -> list[dict]:
    """Kadro tablosu: kod → kurum satırları → unvan → il → ilçe → teşkilat
    → kontenjan → nitelik kodları (4 haneli gruplar, çok satır olabilir)."""
    from unisense.domain.geo import REGIONS
    cities = {c.upper() for cs in REGIONS.values() for c in cs}

    doc = fitz.open(path)
    records: list[dict] = []
    cur: dict | None = None
    text_buf: list[str] = []
    kontenjan_seen = False

    def _flush() -> None:
        nonlocal cur, text_buf, kontenjan_seen
        if cur and cur.get("nitelikler"):
            records.append(cur)
        cur, text_buf, kontenjan_seen = None, [], False

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line:
                continue
            if _KADRO_RE.match(line):
                _flush()
                duzey, ptur = _LEVEL_BY_PREFIX.get(line[0], ("?", "?"))
                cur = {"kadro_kodu": line, "donem": DONEM, "duzey": duzey,
                       "puan_turu": ptur, "kurum": "", "unvan": "", "il": "",
                       "ilce": "", "kontenjan": None, "nitelikler": []}
                continue
            if cur is None:
                continue
            if _KURUMKODU_RE.match(line) and not text_buf:
                continue  # kurum dosya kodu — gereksiz
            # Nitelik kodları (kontenjandan sonra gelen 4 haneli gruplar)
            if kontenjan_seen and _NITELIK_LINE_RE.match(line):
                cur["nitelikler"].extend(line.split())
                continue
            if not kontenjan_seen and _KONTENJAN_RE.match(line) and cur["il"]:
                cur["kontenjan"] = int(line)
                kontenjan_seen = True
                continue
            up = line.upper()
            if up in _TESKILAT:
                continue
            if up in cities or up == "TÜM İLÇELER":
                if not cur["il"] and up in cities:
                    cur["il"] = up
                    # il görülünce: buffer'ın son satırı unvan, öncesi kurum
                    if text_buf:
                        cur["unvan"] = text_buf[-1]
                        cur["kurum"] = " ".join(text_buf[:-1]).strip()
                elif cur["il"]:
                    cur["ilce"] = line
                continue
            if cur["il"] and not kontenjan_seen:
                cur["ilce"] = (cur["ilce"] + " " + line).strip()
                continue
            text_buf.append(line)
    _flush()
    return records


_NITELIK_HEADERS = {"Nitelik", "Kodu", "ÖĞRENİM KOŞULU", "Mezuniyet Alanı Kodları"}


# Nitelik tablosu kolon sınırları (ÖSYM 2026/1 sayfa düzeni, x koordinatı pt):
#   Nitelik Kodu ≈ 30 | ÖĞRENİM KOŞULU (açıklama) ≈ 56–270 | Alan Kodları ≥ 275
_NITELIK_KOD_X_MAX = 50.0    # x < bu → nitelik kodu kolonu (sol kenar)
_NITELIK_ALAN_X_MIN = 275.0  # x ≥ bu → Mezuniyet Alanı Kodları grid'i


def _parse_nitelik(path: Path, duzey: str) -> dict[str, dict]:
    """Nitelik sözlüğü: kod → açıklama + MEZUNİYET ALAN KODLARI.

    KOORDİNAT-BAZLI (BULGU #1): önceki satır-bazlı parser get_text() ile
    kolonları düzlüyordu; açıklama "." ile bitince sonraki tek 4-haneli ALAN
    kodunu 'yeni nitelik kodu' sanıp kayma yapıyordu → 55 kod düşüyordu.
    Artık her nitelik bir y-satır bandı: kod (x<50) çapa, açıklama (50≤x<275)
    ve alan kodları (x≥275) o banda göre atanır — kolonlar asla karışmaz.
    """
    doc = fitz.open(path)
    pages_words = [page.get_text("words") for page in doc]

    # Alan grid'inin en sol kolonu PDF'e göre değişir (lisans~274, önlisans~303,
    # ort~406). 4-haneli kodlar grid'de düzenli kolonlara hizalanır (her satır
    # aynı x) → sık tekrar eden (≥5) en soldaki x kolonu. Açıklamadaki nadir
    # 4-haneli sayı (ör. "2547 sayılı kanun") bir kolona hizalanmadığı için elenir.
    from collections import Counter
    x_counts: Counter = Counter()
    for words in pages_words:
        for w in words:
            if re.fullmatch(r"\d{4}", w[4]) and w[0] >= 250.0:
                x_counts[round(w[0])] += 1
    grid_cols = [x for x, c in x_counts.items() if c >= 5]
    alan_x_min = (min(grid_cols) - 5.0) if grid_cols else _NITELIK_ALAN_X_MIN

    # code -> {"desc": [(y,x,text)], "alan": [(y,x,code)]}
    entries: dict[str, dict[str, list]] = {}

    for words in pages_words:
        # Bu sayfadaki nitelik kodu çapaları (sol kolon, 4-hane), y'ye göre sıralı
        anchors = sorted(
            ((w[1], w[4]) for w in words
             if w[0] < _NITELIK_KOD_X_MAX and re.fullmatch(r"\d{4}", w[4])),
            key=lambda t: t[0],
        )
        if not anchors:
            continue
        anchor_ys = [a[0] for a in anchors]
        anchor_codes = [a[1] for a in anchors]

        def _owner(y: float, _ys=anchor_ys, _codes=anchor_codes) -> str:
            # Çapa i, [y_i - 8, y_{i+1} - 8) bandına sahip. Açıklamanın ilk
            # satırı kod baseline'ından ~6pt yukarıda başladığı için -8 kaydırma.
            for i in range(len(_ys) - 1):
                if y < _ys[i + 1] - 8.0:
                    return _codes[i]
            return _codes[-1]

        for w in words:
            x0, y0, txt = w[0], w[1], w[4]
            if x0 < _NITELIK_KOD_X_MAX and re.fullmatch(r"\d{4}", txt):
                continue  # çapa kodunun kendisi
            if y0 < anchor_ys[0] - 8.0:
                continue  # ilk koddan yukarısı = sayfa başlığı/kolon numaraları
            code = _owner(y0)
            e = entries.setdefault(code, {"desc": [], "alan": []})
            if x0 >= alan_x_min and re.fullmatch(r"\d{4}", txt):
                e["alan"].append((y0, x0, txt))
            elif _NITELIK_KOD_X_MAX <= x0 < alan_x_min:
                e["desc"].append((y0, x0, txt))

    out: dict[str, dict] = {}
    for code, e in entries.items():
        desc_sorted = sorted(e["desc"], key=lambda t: (round(t[0] / 3), t[1]))
        text = " ".join(t[2] for t in desc_sorted).strip()
        if len(text) < 10 or text in _NITELIK_HEADERS:
            continue
        alan_sorted = sorted(e["alan"], key=lambda t: (round(t[0] / 3), t[1]))
        alanlar = [t[2] for t in alan_sorted]
        out[code] = {"aciklama": text, "duzey": duzey,
                     "alan_kodlari": list(dict.fromkeys(alanlar))}
    return out


def _parse_kod_ad(path: Path, duzey: str) -> dict[str, dict]:
    """Mezuniyet alanları: 4 haneli kod + ad (dönüşümlü satırlar)."""
    doc = fitz.open(path)
    out: dict[str, dict] = {}
    code: str | None = None
    name_buf: list[str] = []

    def _flush() -> None:
        nonlocal code, name_buf
        if code and name_buf:
            out[code] = {"ad": " ".join(name_buf).strip(), "duzey": duzey}
        code, name_buf = None, []

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line or "Mezun Olunan" in line or "Alan" == line:
                continue
            if re.match(r"^\d{4}$", line):
                _flush()
                code = line
            elif code:
                name_buf.append(line)
    _flush()
    return out


def _parse_ozel_kosullar(path: Path) -> dict[str, str]:
    """Özel koşullar: kod → koşul metni (yaş, YDS, sertifika vb.)."""
    doc = fitz.open(path)
    out: dict[str, str] = {}
    code: str | None = None
    buf: list[str] = []

    def _flush() -> None:
        nonlocal code, buf
        if code and buf:
            text = " ".join(buf).strip()
            if len(text) > 10:
                out[code] = text
        code, buf = None, []

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line or line in {"Kodu", "Nitelik Adı",
                                    "Nitelik Kodları - Özel Koşullar"}:
                continue
            if re.match(r"^\d{4}$", line):
                _flush()
                code = line
            elif code:
                buf.append(line)
    _flush()
    return out


def main() -> None:
    global DONEM
    CACHE.mkdir(parents=True, exist_ok=True)
    s = _session()

    DONEM, page = _discover_kilavuz(s)
    print(f"📡 Aktif kılavuz: {DONEM} → {page[:80]}")
    tablo_pdfs, nitelik_pdfs, ek_pdfs = _find_kilavuz_pdfs(s, page)
    if not tablo_pdfs:
        print("⛔ Kılavuz tabloları bulunamadı (dönem arası olabilir) — çıkılıyor")
        return
    tag = DONEM.replace("/", "_")

    kadrolar: list[dict] = []
    for name, url in tablo_pdfs.items():
        p = _get(s, url, f"k{tag}_{name}.pdf")
        recs = _parse_tablo(p)
        print(f"   {name}: {len(recs)} kadro")
        kadrolar.extend(recs)
    json.dump(kadrolar, open(OUT_KADRO, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(kadrolar)} aktif kadro → {OUT_KADRO}")

    nitelikler: dict[str, dict] = {}
    for duzey, url in nitelik_pdfs.items():
        p = _get(s, url, f"k{tag}_nitelik_{duzey[:3]}.pdf")
        d = _parse_nitelik(p, duzey)
        print(f"   nitelik/{duzey}: {len(d)} kod")
        nitelikler.update(d)
    json.dump(nitelikler, open(OUT_NITELIK, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(nitelikler)} nitelik kodu → {OUT_NITELIK}")

    # Mezuniyet alanları (kod → resmi program adı) — kod bazlı eşleşme için
    alanlar: dict[str, dict] = {}
    for key, duzey in [("mezun_lisans", "lisans"), ("mezun_önlisans", "önlisans"),
                       ("mezun_ortaöğretim", "ortaöğretim")]:
        if key in ek_pdfs:
            p = _get(s, ek_pdfs[key], f"k{tag}_{key}.pdf")
            d = _parse_kod_ad(p, duzey)
            print(f"   {key}: {len(d)} alan")
            alanlar.update(d)
    if alanlar:
        json.dump(alanlar, open(OUT_ALANLAR, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"✅ {len(alanlar)} mezuniyet alanı → {OUT_ALANLAR}")

    # Özel koşullar (yaş/YDS/sertifika şartları) — kadro uyarıları için
    if "ozelkosullar" in ek_pdfs:
        p = _get(s, ek_pdfs["ozelkosullar"], f"k{tag}_ozelkosullar.pdf")
        kosullar = _parse_ozel_kosullar(p)
        json.dump(kosullar, open(OUT_KOSULLAR, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"✅ {len(kosullar)} özel koşul → {OUT_KOSULLAR}")


if __name__ == "__main__":
    main()
