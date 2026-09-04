"""ÖSYM sitesine erişim — ortak oturum, toleranslı indirme, duyuru keşfi.

NEDEN VAR (2026-09-04 tespiti):

1. www.osym.gov.tr yanıtı `Transfer-Encoding: chunked` ile gönderiyor ama
   SONLANDIRICI CHUNK'I HİÇ GÖNDERMİYOR. İçerik tamamen geliyor (~775 KB),
   bağlantı sadece kapanmıyor. Normal `requests.get(...).text` bu yüzden
   read timeout'a düşüp gövdeyi ÇÖPE ATIYOR — scraper'lar "erişilemiyor"
   sanıyordu. fetch_tolerant() gövdeyi akıtarak biriktirir ve sunucu asılınca
   o ana kadar geleni döndürür; HTML parse için fazlasıyla yeterli.

2. ÖSYM URL şemasını değiştirdi: eski `/TR,33774/...-sayisal-bilgiler.html`
   adresleri artık 404, yenisi slug-only (`/kpss20252-bazi-kamu-...`).
   Eski arama endpoint'i (`/arama?_Dil=1&aranan=...`) ana sayfaya 302 atıyor.
   Slug'lar tutarsız (`kpss20252` ama `kpss-20261`; `2025tus` ama `2026tus`)
   → URL ÜRETİLEMEZ, /Duyurular/Index'ten KEŞFEDİLMELİ.

dokuman.osym.gov.tr (PDF sunucusu) sağlıklı ve hızlı; sorun yalnız ana sitede.
"""
from __future__ import annotations

import re
import time

import requests

DUYURULAR_URL = "https://www.osym.gov.tr/Duyurular/Index"
BASE = "https://www.osym.gov.tr"

# Gövde akışını en fazla bu kadar bekle. Sunucu asıldığında read timeout
# zaten daha erken tetiklenir; bu yalnız üst sınır.
READ_BUDGET_S = 45
_CHUNK_TIMEOUT = (15, 10)  # (connect, read)


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
        # dokuman sunucusu Referer olmadan boş döner
        "Referer": "https://www.osym.gov.tr/",
    })
    return s


def fetch_tolerant(s: requests.Session, url: str, budget_s: int = READ_BUDGET_S) -> str:
    """HTML'i indir; sunucu bağlantıyı kapatmazsa o ana kadar geleni döndür.

    Hiç veri gelmediyse boş string döner (çağıran bunu hata sayar).
    """
    chunks: list[bytes] = []
    deadline = time.monotonic() + budget_s
    try:
        r = s.get(url, timeout=_CHUNK_TIMEOUT, stream=True)
        for chunk in r.iter_content(8192):
            chunks.append(chunk)
            if time.monotonic() > deadline:
                break
    except requests.RequestException:
        pass  # elde ne varsa onunla devam — asıl kontrol çağıranda
    return b"".join(chunks).decode("utf-8", "replace")


def discover(s: requests.Session, pattern: str) -> list[tuple[str, str]]:
    """/Duyurular/Index'ten `pattern`'e uyan duyuru linklerini bul.

    pattern: slug'a uygulanan regex (href="/..." içindeki yol).
    Dönen: [(slug, mutlak_url), ...] — sayfadaki sırayla, tekrarsız.
    """
    html = fetch_tolerant(s, DUYURULAR_URL)
    if not html:
        return []
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for m in re.finditer(r'href="(/[^"]+)"', html):
        slug = m.group(1)
        if slug in seen or not re.search(pattern, slug, re.I):
            continue
        seen.add(slug)
        out.append((slug, BASE + slug))
    return out
