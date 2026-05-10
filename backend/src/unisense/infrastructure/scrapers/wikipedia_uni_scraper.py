"""Wikipedia TR üniversite sayfası scraper.

227 üniversite için:
  1. Wikipedia search ile makale başlığını bul
  2. Extract API ile tam metni çek
  3. Bölümlere ayır (giriş, tarihçe, kampüs, fakülteler)
  4. JSON'a kaydet

Çıktı:
  data/raw/wikipedia/universities.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


WIKI_API = "https://tr.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "UniSense-Bot/0.1 (Educational; contact@unisense.example)",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}
DELAY = 1.0  # Wikipedia rate limit koruması (1 sn)


def search_wiki(query: str) -> str | None:
    """Wikipedia'da arama yap; başlığında 'Üniversite' geçen ilk sonucu döndür.

    İki strateji:
    1) Önce direkt başlık var mı kontrol et (page lookup)
    2) Sonra search yap, ama title 'üniversite' içermesi şart
    """
    # 1) Direkt başlık? "İstanbul Teknik Üniversitesi" başlığı varsa direkt döndür
    direct = _direct_title_check(query)
    if direct:
        return direct

    # 2) Search ile (top 5 sonuç)
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 5,
        "format": "json",
    }
    for attempt in range(4):
        try:
            r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
            if r.status_code == 429:
                wait = 2 ** attempt * 3
                print(f"   ⏳ 429, {wait}s bekliyor...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            results = r.json().get("query", {}).get("search", [])
            # Title'da "üniversite" / "yüksekokul" / "enstitü" geçen ilk
            for res in results:
                t = res["title"].lower()
                if any(k in t for k in ["üniversite", "yüksekokul", "enstitü", "fakültesi"]):
                    return res["title"]
            return None  # uygun başlık yok, alakasız
        except Exception as e:
            if attempt < 3:
                time.sleep(2)
                continue
            print(f"   [arama hata] {query}: {e}")
            return None
    return None


def _direct_title_check(query: str) -> str | None:
    """Verilen başlık tam olarak Wikipedia'da var mı? (redirect dahil)"""
    params = {
        "action": "query",
        "titles": query,
        "redirects": "true",
        "format": "json",
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for _, page in pages.items():
            if "missing" in page:
                return None
            title = page.get("title", "")
            # Sadece "üniversite" içeren başlıkları kabul et (kişi/yer karışıklığı önle)
            t = title.lower()
            if any(k in t for k in ["üniversite", "yüksekokul", "enstitü"]):
                return title
        return None
    except Exception:
        return None


def fetch_extract(title: str) -> str | None:
    """Wikipedia makalesinin tam metnini al."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": "true",
        "redirects": "true",
        "format": "json",
    }
    for attempt in range(4):
        try:
            r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 429:
                wait = 2 ** attempt * 3
                time.sleep(wait)
                continue
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                if "missing" in page:
                    return None
                return page.get("extract", "")
        except Exception as e:
            if attempt < 3:
                time.sleep(2)
                continue
            print(f"   [extract hata] {title}: {e}")
            return None
    return None


def split_sections(text: str) -> list[tuple[str, str]]:
    """== Başlık == ile bölümlere ayır."""
    pattern = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    sections = []
    if matches:
        intro_end = matches[0].start()
        intro = text[:intro_end].strip()
        if intro:
            sections.append(("Giriş", intro))
    else:
        if text.strip():
            sections.append(("Giriş", text.strip()))
        return sections

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append((heading, content))

    return sections


SKIP_HEADINGS = {
    "Kaynakça", "Referanslar", "Dış bağlantılar", "Ayrıca bakınız",
    "Notlar", "Kaynaklar", "Galeri", "Resimler", "Dipnotlar",
}


def is_useful(text: str) -> bool:
    if len(text) < 100:
        return False
    if text.count("|") > len(text) / 30:
        return False
    return True


def turkish_lower(s: str) -> str:
    """Türkçe-doğru küçük harf çevirimi.
    Python default `lower()` 'I' → 'i' yapar (yanlış).
    Türkçede 'I' → 'ı' (dotless), 'İ' → 'i' (dotted).
    """
    return s.replace("I", "ı").replace("İ", "i").lower()


def turkish_title(s: str) -> str:
    """Türkçe-safe title case: her kelimenin ilk harfi büyük, gerisi küçük."""
    out = []
    for w in s.split():
        if not w:
            continue
        first = w[0]  # büyük kalır (zaten ÖSYM'de büyükti)
        rest = turkish_lower(w[1:])
        out.append(first + rest)
    return " ".join(out)


def normalize_uni_name_for_search(name: str) -> str:
    """ÖSYM formatından Wikipedia search formatına çevir.
    'ACIBADEM MEHMET ALİ AYDINLAR ÜNİVERSİTESİ (İSTANBUL)' → 'Acıbadem Mehmet Ali Aydınlar Üniversitesi'
    """
    # 1) Şehir parantezi temizle
    s = re.sub(r"\s*\([^)]+\)\s*$", "", name)
    # 2) Türkçe-safe title case
    return turkish_title(s)


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    unis_file = project_root / "data" / "processed" / "universities.json"
    out_dir = project_root / "data" / "raw" / "wikipedia"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not unis_file.exists():
        print(f"❌ {unis_file} bulunamadı. Önce transform_yokatlas çalıştır.")
        return

    universities = json.load(open(unis_file, encoding="utf-8"))
    print(f"📚 {len(universities)} üniversite için Wikipedia taraması")
    print("=" * 60)

    output: list[dict] = []
    found = 0
    not_found = 0

    for i, uni in enumerate(universities, 1):
        name = uni["name"]
        search_query = normalize_uni_name_for_search(name)
        print(f"[{i}/{len(universities)}] {search_query[:60]:<60} ...", end=" ", flush=True)

        # 1) Search
        title = search_wiki(search_query)
        time.sleep(DELAY)

        if not title:
            print("❌ bulunamadı")
            not_found += 1
            output.append({
                "code": uni["code"],
                "name": name,
                "wikipedia_title": None,
                "extract": None,
                "sections": [],
            })
            continue

        # 2) Extract
        extract = fetch_extract(title)
        time.sleep(DELAY)

        if not extract or len(extract) < 200:
            print(f"⚠️ kısa/boş ({title})")
            not_found += 1
            output.append({
                "code": uni["code"],
                "name": name,
                "wikipedia_title": title,
                "extract": extract,
                "sections": [],
            })
            continue

        # 3) Bölümlere ayır
        sections = split_sections(extract)
        useful_sections = []
        for heading, content in sections:
            if heading in SKIP_HEADINGS:
                continue
            if not is_useful(content):
                continue
            useful_sections.append({"heading": heading, "content": content})

        output.append({
            "code": uni["code"],
            "name": name,
            "wikipedia_title": title,
            "wikipedia_url": f"https://tr.wikipedia.org/wiki/{title.replace(' ', '_')}",
            "extract_length": len(extract),
            "section_count": len(useful_sections),
            "sections": useful_sections,
        })
        print(f"✓ {title[:30]} ({len(useful_sections)} bölüm, {len(extract)} char)")
        found += 1

        # Her 20 üniversitede bir ara kayıt
        if i % 20 == 0:
            with open(out_dir / "universities.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

    # Final kayıt
    out_file = out_dir / "universities.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"✅ Tamamlandı")
    print(f"   ✓ Bulundu: {found}")
    print(f"   ❌ Bulunamadı: {not_found}")
    print(f"   📁 {out_file}")


if __name__ == "__main__":
    main()
