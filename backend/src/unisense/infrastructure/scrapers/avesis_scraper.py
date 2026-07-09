"""Avesis (YÖK Akademisyen) scraper — top üniversiteler için.

Strateji:
  1. Önce her üninin Avesis subdomain'i var mı kontrol et
  2. Akademisyen listesi sayfası (researchers, /yardim/) ara
  3. İlk 100 akademisyeni çek (URL + isim + ünvan + bölüm)
  4. JSON'a kaydet

Top 30 üni hedefli (zaman/kapsama dengesi).
Her üninin yapısı farklı olduğu için "best-effort" — hata olursa atla.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}
TIMEOUT = 12

# Her üniversitenin Avesis subdomain pattern'i — manuel haritalanmış
# (Hepsinde olmayabilir; deneme bazlı)
TOP_UNIVERSITIES = [
    # (uni_code, uni_name, avesis_url)
    ("122571", "Orta Doğu Teknik Üniversitesi (ODTÜ)", "https://avesis.metu.edu.tr"),
    ("115069", "İstanbul Teknik Üniversitesi (İTÜ)", "https://avesis.itu.edu.tr"),
    ("106933", "Hacettepe Üniversitesi", "https://avesis.hacettepe.edu.tr"),
    ("101023", "Ankara Üniversitesi", "https://avesis.ankara.edu.tr"),
    ("103998", "Boğaziçi Üniversitesi", "https://avesis.boun.edu.tr"),
    ("116147", "İzmir Ekonomi Üniversitesi", "https://avesis.ieu.edu.tr"),
    ("105118", "Bahçeşehir Üniversitesi", "https://avesis.bahcesehir.edu.tr"),
    ("106110", "Galatasaray Üniversitesi", "https://avesis.gsu.edu.tr"),
    ("105528", "Bilkent Üniversitesi", "https://avesis.bilkent.edu.tr"),
    ("117200", "Marmara Üniversitesi", "https://avesis.marmara.edu.tr"),
    ("118122", "Kırklareli Üniversitesi", "https://avesis.klu.edu.tr"),
    ("260621", "Gebze Teknik Üniversitesi", "https://avesis.gtu.edu.tr"),
    ("117218", "Yıldız Teknik Üniversitesi", "https://avesis.yildiz.edu.tr"),
    ("173496", "İstanbul Medeniyet Üniversitesi", "https://avesis.medeniyet.edu.tr"),
    ("339997", "Eskişehir Teknik Üniversitesi", "https://avesis.eskisehir.edu.tr"),
    ("339979", "Konya Teknik Üniversitesi", "https://avesis.ktun.edu.tr"),
    ("105024", "Bilecik Şeyh Edebali Üniversitesi", "https://avesis.bilecik.edu.tr"),
    ("109040", "Çukurova Üniversitesi", "https://avesis.cu.edu.tr"),
    ("116950", "Karabük Üniversitesi", "https://avesis.karabuk.edu.tr"),
    ("123456", "Selçuk Üniversitesi", "https://avesis.selcuk.edu.tr"),
    ("114218", "Hitit Üniversitesi", "https://avesis.hitit.edu.tr"),
    ("122395", "Ordu Üniversitesi", "https://avesis.odu.edu.tr"),
    ("117200", "Erciyes Üniversitesi", "https://avesis.erciyes.edu.tr"),
    ("106545", "Çanakkale Onsekiz Mart Üniversitesi", "https://avesis.comu.edu.tr"),
    ("258560", "Akdeniz Üniversitesi", "https://avesis.akdeniz.edu.tr"),
    ("101458", "Süleyman Demirel Üniversitesi", "https://avesis.sdu.edu.tr"),
    ("116950", "Atatürk Üniversitesi", "https://avesis.atauni.edu.tr"),
    ("116950", "Dokuz Eylül Üniversitesi", "https://avesis.deu.edu.tr"),
    ("123412", "Ege Üniversitesi", "https://avesis.ege.edu.tr"),
    ("116950", "Sakarya Üniversitesi", "https://avesis.sakarya.edu.tr"),
]


def check_avesis_alive(url: str) -> bool:
    """Avesis subdomain canlı mı?"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        return r.status_code in (200, 301, 302) and ("avesis" in r.text.lower() or "araştırmac" in r.text.lower())
    except Exception:
        return False


def fetch_researchers_list(base_url: str, max_count: int = 50) -> list[dict]:
    """Avesis araştırmacı listesi sayfasından isim + URL + bölüm çek.

    Tipik URL: /araştırmacı/listele veya /researchers
    """
    candidates = [
        f"{base_url}/araştırmacı",
        f"{base_url}/arastirmaci",
        f"{base_url}/researchers",
        f"{base_url}/araştırmacılar",
        f"{base_url}/arastirmacilar",
        f"{base_url}/profile",
    ]

    researchers = []
    for url in candidates:
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")

            # Akademisyen kartı pattern'leri (Avesis tipik HTML)
            cards = soup.find_all(["div", "article", "tr"], class_=re.compile(r"researcher|akademisyen|kart|card|user", re.I))
            if not cards:
                # Fallback: sayfadaki tüm linklerden /araştırmacı/<id> pattern'ini çıkar
                links = soup.find_all("a", href=re.compile(r"/araştırmacı/|/arastirmaci/|/researcher/", re.I))
                for link in links[:max_count]:
                    href = link.get("href", "")
                    name = link.get_text(strip=True)
                    if name and len(name) > 5 and len(name) < 80:
                        researchers.append({
                            "name": name,
                            "profile_url": href if href.startswith("http") else f"{base_url}{href}",
                            "title": "",
                            "department": "",
                        })
            else:
                for card in cards[:max_count]:
                    name_el = card.find(["h2", "h3", "h4", "a", "strong"])
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)
                    if not name or len(name) < 5:
                        continue
                    title_el = card.find(string=re.compile(r"Prof|Doç|Dr\.|Öğr", re.I))
                    dept_el = card.find(string=re.compile(r"Bölüm|Fakülte|Anabilim", re.I))
                    profile_link = name_el.get("href") if name_el.name == "a" else card.find("a", href=True)
                    href = profile_link if isinstance(profile_link, str) else (profile_link.get("href") if profile_link else "")
                    researchers.append({
                        "name": name,
                        "profile_url": href if href and href.startswith("http") else f"{base_url}{href}" if href else "",
                        "title": title_el.strip() if title_el else "",
                        "department": dept_el.strip() if dept_el else "",
                    })
            if researchers:
                return researchers[:max_count]
        except Exception:
            continue
    return researchers


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    out_dir = project_root / "data" / "raw" / "avesis"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("👨‍🏫 Avesis Scraper — Top 30 Üniversite")
    print("=" * 60)

    all_data = []
    success = 0
    failed = 0

    for i, (uni_code, uni_name, base_url) in enumerate(TOP_UNIVERSITIES, 1):
        print(f"\n[{i}/{len(TOP_UNIVERSITIES)}] {uni_name[:50]:<50} ({base_url})")

        if not check_avesis_alive(base_url):
            print("   ❌ Site cevap vermiyor")
            failed += 1
            all_data.append({
                "university_code": uni_code,
                "university_name": uni_name,
                "avesis_url": base_url,
                "alive": False,
                "researchers": [],
            })
            continue

        researchers = fetch_researchers_list(base_url, max_count=30)
        print(f"   ✓ {len(researchers)} araştırmacı")
        all_data.append({
            "university_code": uni_code,
            "university_name": uni_name,
            "avesis_url": base_url,
            "alive": True,
            "researcher_count": len(researchers),
            "researchers": researchers,
        })
        if researchers:
            success += 1
        time.sleep(1.0)

    out_file = out_dir / "academics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"✅ Tamamlandı: {success} başarılı, {failed} başarısız")
    print(f"   Toplam araştırmacı: {sum(len(d.get('researchers', [])) for d in all_data)}")
    print(f"📁 {out_file}")


if __name__ == "__main__":
    main()
