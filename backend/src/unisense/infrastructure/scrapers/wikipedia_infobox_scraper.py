"""Wikipedia TR üniversite infobox parser.

Mevcut data/raw/wikipedia/universities.json içindeki wikipedia_title alanlarını
kullanarak her üniversite için Wikipedia infobox HTML'ini parse eder ve
website, kuruluş yılı, logo URL, telefon, e-posta, adres çıkarır.

Çıktı:
  data/raw/wikipedia/infobox.json

Kullanım:
  python -m unisense.infrastructure.scrapers.wikipedia_infobox_scraper
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


WIKI_API = "https://tr.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "UniSense-Bot/0.2 (Educational; https://github.com/BrokyEwing/UniSense)",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}
DELAY = 1.0

LABEL_MAP = {
    "kuruluş": "founded_raw",
    "kuruluş tarihi": "founded_raw",
    "kuruluş yılı": "founded_raw",
    "kurulduğu yıl": "founded_raw",
    "kurulduğu tarih": "founded_raw",
    "açılış": "founded_raw",
    "web sitesi": "website",
    "web adresi": "website",
    "internet sitesi": "website",
    "resmî site": "website",
    "resmi site": "website",
    "telefon": "phone",
    "tel": "phone",
    "e-posta": "email",
    "eposta": "email",
    "e-mail": "email",
    "adres": "address",
    "konum": "address",
    "rektör": "rector",
    "kurucu": "founder",
    "türü": "type_wiki",
    "tür": "type_wiki",
    "öğrenci sayısı": "student_count_raw",
    "öğrenci": "student_count_raw",
    "akademik kadro": "academic_staff_raw",
    "personel sayısı": "staff_count_raw",
    "renkleri": "colors",
    "renk": "colors",
    "kısaltma": "short_name_wiki",
    "kısa adı": "short_name_wiki",
    "amblem": "logo_raw",
    "logo": "logo_raw",
}


def fetch_parse_html(title: str) -> str | None:
    """Wikipedia parse API'den sayfanın HTML'ini al."""
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "redirects": "true",
    }
    for attempt in range(4):
        try:
            r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=25)
            if r.status_code == 429:
                wait = 2 ** attempt * 3
                print(f"   ⏳ 429, {wait}s bekliyor...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                return None
            return data.get("parse", {}).get("text", {}).get("*", "")
        except Exception as e:
            if attempt < 3:
                time.sleep(2)
                continue
            print(f"   [parse hata] {title}: {e}")
            return None
    return None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_year(text: str) -> int | None:
    """Metinden ilk 4-haneli yıl çıkar (1700-2030 arası)."""
    if not text:
        return None
    m = re.search(r"\b(1[6-9]\d{2}|20[0-3]\d)\b", text)
    return int(m.group(1)) if m else None


def _absolute_url(src: str) -> str:
    """Wikipedia göreceli url'sini mutlak yap."""
    if not src:
        return ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return "https://tr.wikipedia.org" + src
    return src


def parse_infobox(html: str) -> dict[str, Any]:
    """Infobox tablosundan alanları çıkar."""
    out: dict[str, Any] = {}
    if not html:
        return out

    soup = BeautifulSoup(html, "lxml")
    # Üniversite infobox class'ları: infobox, infobox_v2, infobox vcard
    infobox = soup.find("table", class_=re.compile(r"\binfobox\b"))
    if not infobox:
        return out

    # Logo (ilk img veya .infobox-image içindeki)
    img = infobox.find("img")
    if img and img.get("src"):
        out["logo_raw"] = _absolute_url(img["src"])

    # Satırları gez
    for row in infobox.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label_raw = _clean(th.get_text(" ", strip=True)).lower()
        # Türkçe-safe lower zaten requests.get ile geliyor
        if not label_raw:
            continue

        # Label fuzzy match
        key = None
        for label, mapped_key in LABEL_MAP.items():
            if label_raw == label or label_raw.startswith(label + " ") or label in label_raw:
                key = mapped_key
                break
        if not key:
            continue

        # Değer
        if key == "website":
            link = td.find("a", href=True)
            if link:
                out["website"] = link["href"].strip()
            else:
                out["website"] = _clean(td.get_text(" ", strip=True))
        elif key == "email":
            email_text = _clean(td.get_text(" ", strip=True))
            email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", email_text)
            out["email"] = email_match.group(0) if email_match else email_text
        elif key == "phone":
            phone_text = _clean(td.get_text(" ", strip=True))
            out["phone"] = phone_text
        elif key == "founded_raw":
            out["founded_raw"] = _clean(td.get_text(" ", strip=True))
            year = _extract_year(out["founded_raw"])
            if year:
                out["founded_year"] = year
        else:
            out[key] = _clean(td.get_text(" ", strip=True))

    return out


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    wiki_file = project_root / "data" / "raw" / "wikipedia" / "universities.json"
    out_file = project_root / "data" / "raw" / "wikipedia" / "infobox.json"

    if not wiki_file.exists():
        print(f"❌ {wiki_file} bulunamadı. Önce wikipedia_uni_scraper çalıştır.")
        return

    universities = json.load(open(wiki_file, encoding="utf-8"))
    targets = [u for u in universities if u.get("wikipedia_title")]
    print(f"📚 {len(targets)}/{len(universities)} üniversite için infobox parse")
    print("=" * 60)

    output: list[dict] = []
    found = 0
    no_infobox = 0

    # Önceki çıktıyı koru (idempotent yeniden çalıştırma için)
    existing: dict[str, dict] = {}
    if out_file.exists():
        try:
            existing = {x["code"]: x for x in json.load(open(out_file, encoding="utf-8"))}
        except Exception:
            existing = {}

    for i, uni in enumerate(targets, 1):
        code = uni["code"]
        title = uni["wikipedia_title"]
        name_preview = uni["name"][:55]
        print(f"[{i}/{len(targets)}] {name_preview:<55} ...", end=" ", flush=True)

        # Skip if already done and has data
        if code in existing and existing[code].get("infobox"):
            print("✓ (cached)")
            output.append(existing[code])
            found += 1
            continue

        html = fetch_parse_html(title)
        time.sleep(DELAY)

        if not html:
            print("❌ parse hata")
            output.append({"code": code, "name": uni["name"], "wikipedia_title": title, "infobox": {}})
            no_infobox += 1
            continue

        infobox = parse_infobox(html)

        if not infobox:
            print("⚠️ infobox yok")
            no_infobox += 1
        else:
            bits = []
            if "founded_year" in infobox:
                bits.append(f"{infobox['founded_year']}")
            if "website" in infobox:
                bits.append("web")
            if "logo_raw" in infobox:
                bits.append("logo")
            if "phone" in infobox:
                bits.append("tel")
            print(f"✓ {','.join(bits) if bits else 'boş'}")
            found += 1

        output.append({
            "code": code,
            "name": uni["name"],
            "wikipedia_title": title,
            "infobox": infobox,
        })

        # Her 20 üniversitede ara kayıt
        if i % 20 == 0:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

    # Final kayıt
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print("✅ Tamamlandı")
    print(f"   ✓ Infobox bulundu: {found}")
    print(f"   ⚠️  Infobox yok/boş: {no_infobox}")
    print(f"   📁 {out_file}")


if __name__ == "__main__":
    main()
