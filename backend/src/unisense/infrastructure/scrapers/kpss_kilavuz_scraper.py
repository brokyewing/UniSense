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
CACHE = BACKEND / ".cache" / "kpss"

DONEM = "2026/1"
BASE = "https://dokuman.osym.gov.tr/pdfdokuman/2026/KPSS/TERCIH1/"
TABLO_PDFS = {  # kadro kodu ilk hanesi → düzey/puan türü zaten koddan çıkarılıyor
    "tablo1": BASE + "tablo1_t1d03072026.pdf",
    "tablo2": BASE + "tablo2_t1d03062026.pdf",
    "tablo3": BASE + "tablo3_t1d03072026.pdf",
}
NITELIK_PDFS = {
    "lisans": BASE + "lisans-nitelik_t1d03072026.pdf",
    "önlisans": BASE + "onlisans-nitelik_t1d03072026.pdf",
    "ortaöğretim": BASE + "ortaogretim-nitelik_t1d03072026.pdf",
}

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


def _parse_nitelik(path: Path, duzey: str) -> dict[str, dict]:
    """Nitelik sözlüğü: 4 haneli kod → açıklama metni.

    Sayfa düzeni: kod → çok satırlı açıklama ("... mezun olmak.") →
    mezuniyet alanı kodları (4'lü sayı dizileri). KURAL: 4 haneli satır,
    mevcut açıklama '.' ile bitmişse (veya hiç açıklama yoksa) YENİ koddur;
    aksi halde açıklama sonundaki alan kodudur (atılır).
    """
    doc = fitz.open(path)
    out: dict[str, dict] = {}
    code: str | None = None
    buf: list[str] = []

    def _text() -> str:
        return " ".join(buf).strip()

    def _flush() -> None:
        nonlocal code, buf
        if code:
            text = re.sub(r"(\s\d{4})+\s*$", "", _text()).strip()
            if len(text) > 15:
                out[code] = {"aciklama": text, "duzey": duzey}
        code, buf = None, []

    for page in doc:
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if (not line or line in _NITELIK_HEADERS
                    or re.match(r"^\d{1,2}(\s+\d{1,2})*$", line)   # sütun no'ları
                    or "ARANAN NİTELİKLER" in line.upper()):
                continue
            if re.match(r"^\d{4}(\s+\d{4})*$", line):
                first = line.split()[0]
                desc_done = _text().endswith((".", ":"))
                if code is None or (desc_done and re.match(r"^\d{4}$", line)):
                    _flush()
                    code = first
                # aksi halde alan kodları — açıklamaya katılmaz
                continue
            if code:
                buf.append(line)
    _flush()
    return out


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    s = _session()

    kadrolar: list[dict] = []
    for name, url in TABLO_PDFS.items():
        p = _get(s, url, f"t2026_{name}.pdf")
        recs = _parse_tablo(p)
        print(f"   {name}: {len(recs)} kadro")
        kadrolar.extend(recs)
    json.dump(kadrolar, open(OUT_KADRO, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(kadrolar)} aktif kadro → {OUT_KADRO}")

    nitelikler: dict[str, dict] = {}
    for duzey, url in NITELIK_PDFS.items():
        p = _get(s, url, f"t2026_nitelik_{duzey[:3]}.pdf")
        d = _parse_nitelik(p, duzey)
        print(f"   nitelik/{duzey}: {len(d)} kod")
        nitelikler.update(d)
    json.dump(nitelikler, open(OUT_NITELIK, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(nitelikler)} nitelik kodu → {OUT_NITELIK}")


if __name__ == "__main__":
    main()
