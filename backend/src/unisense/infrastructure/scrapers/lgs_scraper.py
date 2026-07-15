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
from datetime import datetime, timezone
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
    """Okul adından lise türünü çıkarır (öncelik sırası önemli — 'imam hatip'
    EN ÖNCE: 'Fen, Sosyal Bilimler ve Teknoloji Anadolu İmam Hatip Lisesi' gibi
    adlar sosyal/fen içerse de okul idari olarak İmam Hatip'tir)."""
    f = _fold(okul)
    if "imam hatip" in f:
        return "imam_hatip"
    if "sosyal bilimler" in f:
        return "sosyal"
    if "fen lisesi" in f:
        return "fen"
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


def _lise_key(lise: dict) -> str:
    """Okul kaydını yıllar arası eşlemek için kararlı anahtar (kod alanı yok)."""
    return _fold(f"{lise['okul']}|{lise.get('ilce', '')}|{lise.get('dil', '')}")


def _merge_history(yeni: list[dict], eski: list[dict]) -> None:
    """Önceki JSON'daki trend yıllarını yeni kayıtlara taşır (yerinde).

    Kaynak site yalnız son ~4 yılı gösterir; her yıllık cron'da eski yıllar
    düşer. Bu birleştirme sayesinde arşiv sitede birikir: aynı yıl için YENİ
    veri kazanır, yeni scrape'te olmayan eski yıllar korunur.
    """
    eski_map = {_lise_key(x): x for x in eski}
    tasinan = 0
    for lise in yeni:
        onceki = eski_map.get(_lise_key(lise))
        if not onceki:
            continue
        mevcut_yillar = {t["yil"] for t in lise["trend"]}
        for t in onceki.get("trend", []):
            if t["yil"] not in mevcut_yillar:
                lise["trend"].append(t)
                tasinan += 1
        lise["trend"].sort(key=lambda t: -t["yil"])  # en güncel önce
    if tasinan:
        print(f"  ↺ arşivden {tasinan} eski yıl kaydı korundu")


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
    # Önceki dosyadaki eski yılları koru (kaynak site eski yılları düşürür)
    if OUT.exists():
        try:
            eski = json.loads(OUT.read_text(encoding="utf-8")).get("liseler", [])
            _merge_history(all_liseler, eski)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ arşiv birleştirme atlandı: {e}")
    # En güncel yılı tespit et (trend'lerdeki max yıl) — metinler yıla göre üretilir,
    # böylece yıllık cron'da elle güncelleme gerekmez
    yillar = [t["yil"] for lise in all_liseler for t in lise["trend"]]
    guncel_yil = max(yillar) if yillar else None
    return {
        "guncelleme": datetime.now(timezone.utc).strftime("%Y-%m"),
        "kaynak": "MEB e-Okul taban puan verisi (tabanpuanlari.tr üzerinden derlendi)",
        "not": (
            f"Yüzdelik dilim Türkiye geneli, geçen yıl (LGS {guncel_yil}) verisidir ve TAHMİNÎDİR — "
            "bu yılki taban puanları değişebilir. Yalnızca merkezî sınavla öğrenci alan liseleri "
            "kapsar; adrese dayalı yerleştirme kapsam dışıdır. Resmî tercih: rotamaarif.meb.gov.tr"
        ),
        "yil": guncel_yil,
        "toplam": len(all_liseler),
        "basarisiz_iller": basarisiz,
        "liseler": all_liseler,
    }


_MIN_KAYIT = 1500  # bunun altı = kaynak yapısı değişmiş/erişilemez → YAZMA


def main() -> None:
    data = scrape()
    # Güvenlik tabanları: gözetimsiz cron main'e push ettiği için bozuk/eksik
    # veri eski verinin üzerine YAZILMAZ; exit 1 ile workflow da kırmızı düşer.
    # 1) Herhangi bir il başarısızsa yazma (kısmî veri = o ilin öğrencisine boş sonuç)
    if data["basarisiz_iller"]:
        print(f"\n⛔ {len(data['basarisiz_iller'])} il başarısız "
              f"({', '.join(data['basarisiz_iller'][:5])}…) — {OUT.name} GÜNCELLENMEDİ")
        sys.exit(1)
    # 2) Mutlak taban
    if data["toplam"] < _MIN_KAYIT:
        print(f"\n⛔ Yalnız {data['toplam']} lise (<{_MIN_KAYIT}) — kaynak değişmiş "
              f"olabilir; {OUT.name} GÜNCELLENMEDİ (eski veri korundu)")
        sys.exit(1)
    # 3) Önceki dosyaya göre %90 tabanı (kaynak sessizce daralırsa yakala)
    if OUT.exists():
        try:
            onceki = json.loads(OUT.read_text(encoding="utf-8")).get("toplam", 0)
            if onceki and data["toplam"] < onceki * 0.9:
                print(f"\n⛔ {data['toplam']} < önceki {onceki}×0.9 — şüpheli daralma; "
                      f"{OUT.name} GÜNCELLENMEDİ")
                sys.exit(1)
        except Exception:  # noqa: BLE001, S110
            pass
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
