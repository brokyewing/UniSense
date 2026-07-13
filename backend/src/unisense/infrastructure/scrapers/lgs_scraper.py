"""LGS lise taban puanları / yüzdelik dilimleri → lgs_liseler.json.

Kaynak: MEB e-Okul "Okul Nakil Boş Kontenjan ve Taban Puan Bilgileri" verisi
(tabanpuanlari.tr üzerinden derlenmiş; il başına tek HTML tablo, robots.txt açık).
Nihai veri MEB'e aittir — çıktıda ve UI'de kaynak MEB olarak gösterilir.

Sadece merkezî sınavla (LGS) öğrenci alan liseler bu tabloda yer alır; adrese
dayalı yerleştirmeyle öğrenci alan okullar (öğrencilerin ~%85'i) burada YOKTUR.

Tablo düzeni (her il sayfası, 9 sütun):
    Trend | Okul | İl<br>İlçe | Öğretim Türü | Yıllar | Taban Puan | Yüzdelik | Pansiyon | Kont
Çok yıllı hücreler <br> ile ayrılır; ilk değer en güncel yıldır (2025).

Yüzdelik dilim TÜRKİYE GENELİ'dir (tercihte belirleyici metrik; ham puandan
yıldan yıla daha stabildir → öneri motoru bunu kullanır).

Çıktı: data/processed/lgs_liseler.json
Kullanım: python -m unisense.infrastructure.scrapers.lgs_scraper
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

    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "https://tabanpuanlari.tr/lise/{}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "lgs_liseler.json"

# 81 il (tabanpuanlari.tr slug formatı)
IL_SLUGS = [
    "adana", "adiyaman", "afyonkarahisar", "agri", "aksaray", "amasya", "ankara",
    "antalya", "ardahan", "artvin", "aydin", "balikesir", "bartin", "batman",
    "bayburt", "bilecik", "bingol", "bitlis", "bolu", "burdur", "bursa", "canakkale",
    "cankiri", "corum", "denizli", "diyarbakir", "duzce", "edirne", "elazig",
    "erzincan", "erzurum", "eskisehir", "gaziantep", "giresun", "gumushane",
    "hakkari", "hatay", "igdir", "isparta", "istanbul", "izmir", "kahramanmaras",
    "karabuk", "karaman", "kars", "kastamonu", "kayseri", "kilis", "kirikkale",
    "kirklareli", "kirsehir", "kocaeli", "konya", "kutahya", "malatya", "manisa",
    "mardin", "mersin", "mugla", "mus", "nevsehir", "nigde", "ordu", "osmaniye",
    "rize", "sakarya", "samsun", "sanliurfa", "siirt", "sinop", "sirnak", "sivas",
    "tekirdag", "tokat", "trabzon", "tunceli", "usak", "van", "yalova", "yozgat",
    "zonguldak",
]


def _clean(html_fragment: str) -> str:
    """HTML etiketlerini soyar, boşlukları normalize eder."""
    text = re.sub(r"<[^>]+>", " ", html_fragment)
    return re.sub(r"\s+", " ", text).strip()


def _split_years(td_html: str) -> list[str]:
    """<br> ile ayrılmış çok yıllı hücreyi parçalara böler (ilk = en güncel yıl)."""
    parts = re.split(r"<br\s*/?>", td_html, flags=re.I)
    return [_clean(p) for p in parts if _clean(p)]


def _num(s: str) -> float | None:
    """'483.280' / '0,53' → float. Türkçe ondalık virgülü noktaya çevirir."""
    s = s.strip().replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


_FOLD_TR = {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"}


def _fold(s: str) -> str:
    """Türkçe → ascii küçük harf (İ/I büyük-harf tuzağını atlar)."""
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return "".join(_FOLD_TR.get(c, c) for c in s)


def _classify_tur(okul: str) -> str:
    """Okul adından lise türünü çıkarır (öncelik sırası önemli — imam_hatip ve
    meslek, 'anadolu' içerdikleri için ondan ÖNCE kontrol edilir)."""
    f = _fold(okul)
    if "sosyal bilimler" in f:
        return "sosyal"
    if "fen lisesi" in f:
        return "fen"
    if "imam hatip" in f:
        return "imam_hatip"
    if "guzel sanatlar" in f:
        return "guzel_sanatlar"
    if "spor lisesi" in f:
        return "spor"
    if "mesleki" in f or "meslek" in f or "teknik" in f:
        return "meslek"
    if "anadolu" in f:
        return "anadolu"
    return "diger"


def parse_il(html: str, il_slug: str) -> list[dict]:
    """Bir il sayfasının tablo satırlarını normalize edilmiş kayıtlara çevirir."""
    liseler: list[dict] = []
    # Veri satırları: içinde 9 td olan tr'ler
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", html, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 9:
            continue
        okul = _clean(tds[1])
        if not okul:
            continue
        # İl / İlçe (td2, <br> ile)
        il_ilce = _split_years(tds[2])
        il = il_ilce[0] if il_ilce else il_slug.upper()
        ilce = il_ilce[1] if len(il_ilce) > 1 else ""
        # Öğretim türü / dil (td3): "İngilizce - Kız/Erkek" + <small>4 yıl</small>
        dil = _clean(re.sub(r"<small>.*?</small>", "", tds[3], flags=re.S))
        # Çok yıllı sütunlar
        yillar = _split_years(tds[4])
        tabanlar = _split_years(tds[5])
        yuzdelikler = _split_years(tds[6])
        kontenjanlar = _split_years(tds[8])
        if not yillar or not yuzdelikler:
            continue
        # En güncel yıl = ilk eleman
        taban_puan = _num(tabanlar[0]) if tabanlar else None
        yuzdelik = _num(yuzdelikler[0]) if yuzdelikler else None
        if yuzdelik is None:
            continue
        # Trend: yıl→yüzdelik/puan (sparkline için)
        trend = []
        for i, yil in enumerate(yillar):
            y = _num(yuzdelikler[i]) if i < len(yuzdelikler) else None
            p = _num(tabanlar[i]) if i < len(tabanlar) else None
            yil_i = _num(yil)
            if yil_i and y is not None:
                trend.append({"yil": int(yil_i), "yuzdelik": y, "puan": p})
        liseler.append({
            "okul": okul,
            "il": il,
            "ilce": ilce,
            "tur": _classify_tur(okul),
            "dil": dil,
            "taban_puan": taban_puan,
            "yuzdelik": yuzdelik,
            "kontenjan": int(_num(kontenjanlar[0])) if kontenjanlar and _num(kontenjanlar[0]) else None,
            "pansiyon": _clean(tds[7]) or None,
            "trend": trend,
        })
    return liseler


def scrape() -> dict:
    all_liseler: list[dict] = []
    basarisiz: list[str] = []
    for i, slug in enumerate(IL_SLUGS, 1):
        try:
            r = requests.get(BASE.format(slug), headers=HEADERS, timeout=30)
            r.raise_for_status()
            kayitlar = parse_il(r.text, slug)
            all_liseler.extend(kayitlar)
            print(f"[{i:2}/81] {slug:16} {len(kayitlar):4} lise")
        except Exception as e:  # noqa: BLE001
            basarisiz.append(slug)
            print(f"[{i:2}/81] {slug:16} HATA: {type(e).__name__}: {e}")
        time.sleep(0.7)  # kibar gecikme
    # En güncel yılı tespit et (trend'lerdeki max yıl)
    yillar = [t["yil"] for lise in all_liseler for t in lise["trend"]]
    guncel_yil = max(yillar) if yillar else None
    return {
        "guncelleme": "2026-07",
        "kaynak": "MEB e-Okul taban puan verisi (tabanpuanlari.tr üzerinden derlendi)",
        "not": (
            "Yüzdelik dilim Türkiye geneli, geçen yıl (LGS 2025) verisidir ve TAHMİNÎDİR — "
            "bu yılki taban puanları değişebilir. Yalnızca merkezî sınavla öğrenci alan liseleri "
            "kapsar; adrese dayalı yerleştirme kapsam dışıdır. Resmî tercih: rotamaarif.meb.gov.tr"
        ),
        "yil": guncel_yil,
        "toplam": len(all_liseler),
        "basarisiz_iller": basarisiz,
        "liseler": all_liseler,
    }


def main() -> None:
    data = scrape()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tur_sayim: dict[str, int] = {}
    for lise in data["liseler"]:
        tur_sayim[lise["tur"]] = tur_sayim.get(lise["tur"], 0) + 1
    print(f"\n✓ {data['toplam']} lise → {OUT}")
    print(f"  Yıl: {data['yil']} | Başarısız il: {len(data['basarisiz_iller'])}")
    print(f"  Tür dağılımı: {dict(sorted(tur_sayim.items(), key=lambda x: -x[1]))}")


if __name__ == "__main__":
    main()
