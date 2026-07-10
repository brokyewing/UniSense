"""İŞKUR Meslek Bilgi Kitapçıkları (MEB aynası) → bölüm rehberi verisi.

Kaynak: meslegimhayatim.meb.gov.tr (MEB kariyer portalı, İŞKUR kitapçıklarının
resmi yayını — esube.iskur.gov.tr WAF'la bot erişimini reddettiği için
kitapçıkların MEB'deki resmi kopyası kullanılıyor).

8 cilt PDF indirilir, font boyutundan meslek başlıkları tespit edilir,
her mesleğin metni çıkarılır ve bölüm gruplarıyla (compass taxonomy)
fold'lu ad eşleştirmesi yapılır. Sadece GÜVENLİ eşleşmeler alınır
(birebir ad ya da tam token kapsaması) — yanlış bölüme resmi içerik
yapıştırmak halüsinasyondan beter.

Çıktı: data/processed/iskur_guides.json
Kullanım: python -m unisense.infrastructure.scrapers.iskur_mbk_scraper
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
import requests

from unisense.core.text import fold_tr

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BACKEND = Path(__file__).resolve().parents[4]
OUT = BACKEND / "data" / "processed" / "iskur_guides.json"
CACHE = BACKEND / ".cache" / "iskur_mbk"

# MEB kariyer portalındaki 8 cilt (A'dan Z'ye)
INDEX_PAGE = ("https://kumlucakizanadoluihl.meb.k12.tr/icerikler/"
              "meslek-bilgi-kitapciklari-adan-zye-iskur_12668864.html")

MIN_TITLE_SIZE = 20   # meslek başlıkları büyük fontla yazılı
MIN_BODY_CHARS = 300  # bundan kısa meslek metni alınmaz


def _download_pdfs() -> list[Path]:
    CACHE.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    html = s.get(INDEX_PAGE, timeout=60).text
    urls = re.findall(r'href="(https://meslegimhayatim\.meb\.gov\.tr/[^"]*\.pdf)"', html)
    urls = list(dict.fromkeys(urls))
    paths = []
    for i, url in enumerate(urls, 1):
        p = CACHE / f"mbk_{i}.pdf"
        if not p.exists() or p.stat().st_size < 1000:
            print(f"  indiriliyor {i}/{len(urls)}: {url.rsplit('/', 1)[-1]}")
            p.write_bytes(s.get(url, timeout=180).content)
        paths.append(p)
    return paths


def _extract_professions(pdf_path: Path) -> list[dict]:
    """Font boyutu MIN_TITLE_SIZE üstü satırlar = meslek başlığı varsayımı."""
    doc = fitz.open(pdf_path)
    sections: list[dict] = []
    current: dict | None = None

    for page in doc:
        d = page.get_text("dict")
        page_titles = []
        body_parts = []
        for block in d.get("blocks", []):
            for line in block.get("lines", []):
                line_text = "".join(sp["text"] for sp in line.get("spans", [])).strip()
                if not line_text:
                    continue
                max_size = max(sp["size"] for sp in line["spans"])
                if max_size >= MIN_TITLE_SIZE and len(line_text) > 3 and not line_text.isdigit():
                    page_titles.append(line_text)
                else:
                    body_parts.append(line_text)

        title = " ".join(page_titles).strip()
        # Kapak/bölüm ayracı sayfaları ("A-B MESLEK KİTAPÇIĞI") meslek değil
        if title and "KİTAPÇI" in title.upper():
            continue
        if title:
            if current:
                sections.append(current)
            current = {"name": title, "body": []}
        if current:
            current["body"].extend(body_parts)

    if current:
        sections.append(current)

    out = []
    for s in sections:
        body = "\n".join(s["body"])
        # sayfa numarası / tekrar eden altbilgileri temizle
        body = re.sub(r"^\d{1,3}$", "", body, flags=re.M)
        body = re.sub(r"^Meslek Bilgi Kitapçığı$", "", body, flags=re.M)
        body = re.sub(r"Meslek ile ilgili detayları diğer\s*\n?sayfada bulabilirsiniz\.?", "", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        if len(body) >= MIN_BODY_CHARS:
            out.append({"meslek": s["name"].strip(), "content": body})
    return out


# Meslek adındaki jenerik rol kelimeleri — bölüm adında karşılığı yoksa
# fazlalık sayılıp yok sayılabilir (2. aşama eşleşme)
_ROLE_WORDS = {
    "meslek", "elemani", "uzmani", "uzman", "personeli", "gorevlisi",
    "teknikeri", "teknisyeni", "muhendisi", "danismani", "operatoru",
    "sorumlusu", "yoneticisi",
}


def _norm_tokens(name: str) -> set[str]:
    """Eşleştirme için token kümesi (fold'lu; 'ağ', 'iç' gibi kısalar dahil)."""
    toks = set()
    for w in re.findall(r"[a-zçğıöşü]+", fold_tr(name)):
        if len(w) >= 2 and w not in {"ve", "ile"}:
            toks.add(w)
    return toks


def _tok_eq(a: str, b: str) -> bool:
    """Türkçe ek toleransı: 'muhendis(i)' == 'muhendisligi'.

    Önek kuralı: biri diğerinin öneki ve ortak kök ≥5 harf.
    'elektrik' ile 'elektronik' EŞLEŞMEZ (önek değil) — kritik güvenlik.
    """
    if a == b:
        return True
    if len(a) >= 5 and len(b) >= 5:
        return a.startswith(b) or b.startswith(a)
    return False


def _fuzzy_set_equal(x: set[str], y: set[str]) -> bool:
    """Her token'ın karşı kümede fuzzy eşi varsa kümeler eş sayılır."""
    return (all(any(_tok_eq(a, b) for b in y) for a in x)
            and all(any(_tok_eq(b, a) for a in x) for b in y))


def _match_groups(professions: list[dict], groups: list[str]) -> list[dict]:
    """Meslek ↔ bölüm grubu eşleştir — sadece güvenli eşleşmeler."""
    group_tokens = {g: _norm_tokens(g) for g in groups}
    matched: dict[str, dict] = {}

    for prof in professions:
        ptoks = _norm_tokens(prof["meslek"])
        if not ptoks:
            continue
        # 2. aşama için: rol kelimeleri düşülmüş hali (en az 2 anlamlı token
        # kalmalı — "Ağ İşletmeni"→{ag} gibi tekli kalıntılar eşleştirilmez)
        pcore = ptoks - _ROLE_WORDS
        for g, gtoks in group_tokens.items():
            if not gtoks:
                continue
            ok = _fuzzy_set_equal(ptoks, gtoks) or (
                len(pcore) >= 2 and _fuzzy_set_equal(pcore, gtoks)
            )
            if ok:
                # Bir gruba en uzun içerikli meslek metni kalsın
                prev = matched.get(g)
                if prev is None or len(prof["content"]) > len(prev["content"]):
                    matched[g] = {
                        "name": g,
                        "meslek": prof["meslek"],
                        "content": prof["content"],
                    }
    return list(matched.values())


def main() -> None:
    from unisense.application.services.compass_taxonomy import get_taxonomy

    print("📥 MBK kitapçıkları indiriliyor (MEB aynası)...")
    pdfs = _download_pdfs()
    print(f"   {len(pdfs)} cilt")

    professions: list[dict] = []
    for p in pdfs:
        secs = _extract_professions(p)
        professions.extend(secs)
        print(f"   {p.name}: {len(secs)} meslek")
    print(f"📚 Toplam {len(professions)} meslek metni")

    groups = [g["name"] for g in get_taxonomy()["departments"]]
    matched = _match_groups(professions, groups)
    print(f"🔗 Bölüm grubuyla güvenli eşleşen: {len(matched)}")

    json.dump(matched, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ {OUT}")


if __name__ == "__main__":
    main()
