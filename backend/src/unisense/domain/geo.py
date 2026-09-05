"""Türkiye coğrafi haritalar — il, bölge, KKTC.

Sahil/metropol/merkez ilçe metadatası `data/raw/turkey_geo.json` dosyasından gelir.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REGIONS: dict[str, list[str]] = {
    "Marmara": [
        "İSTANBUL", "BURSA", "KOCAELİ", "TEKİRDAĞ", "BALIKESİR", "ÇANAKKALE",
        "EDİRNE", "KIRKLARELİ", "SAKARYA", "YALOVA", "BİLECİK",
    ],
    "Ege": [
        "İZMİR", "MANİSA", "AYDIN", "DENİZLİ", "MUĞLA", "AFYONKARAHİSAR",
        "KÜTAHYA", "UŞAK",
    ],
    "Akdeniz": [
        "ANTALYA", "ADANA", "MERSİN", "HATAY", "BURDUR", "ISPARTA",
        "OSMANİYE", "KAHRAMANMARAŞ",
    ],
    "İç Anadolu": [
        "ANKARA", "KONYA", "KAYSERİ", "ESKİŞEHİR", "AKSARAY", "ÇANKIRI",
        "KIRIKKALE", "KIRŞEHİR", "NEVŞEHİR", "NİĞDE", "SİVAS", "YOZGAT",
        "KARAMAN",
    ],
    "Karadeniz": [
        "SAMSUN", "TRABZON", "ORDU", "GİRESUN", "RİZE", "ARTVİN",
        "BARTIN", "BAYBURT", "BOLU", "ÇORUM", "DÜZCE", "GÜMÜŞHANE",
        "KASTAMONU", "KARABÜK", "SİNOP", "TOKAT", "ZONGULDAK", "AMASYA",
    ],
    "Doğu Anadolu": [
        "ERZURUM", "MALATYA", "ELAZIĞ", "VAN", "AĞRI", "ARDAHAN",
        "BİNGÖL", "BİTLİS", "ERZİNCAN", "HAKKARİ", "IĞDIR", "KARS",
        "MUŞ", "TUNCELİ",
    ],
    "Güneydoğu Anadolu": [
        "GAZİANTEP", "DİYARBAKIR", "ŞANLIURFA", "MARDİN", "BATMAN",
        "ADIYAMAN", "KİLİS", "SİİRT", "ŞIRNAK",
    ],
    "KKTC": [
        "GAZİMAĞUSA", "GİRNE", "LEFKE", "LEFKOŞA", "GÜZELYURT", "İSKELE",
    ],
    "Yurtdışı": [
        # Yurtdışı kamu üniversiteleri
    ],
}


# Aksan/Türkçe-harf katlama tablosu. Kaynaklar il adını farklı yazıyor:
# ilan.gov.tr "İSTANBUL", Jooble/Careerjet gibi yabancı API'ler "Istanbul".
# Düz .upper() bunları eşleştiremiyordu (I ≠ İ) ve bölge sessizce "Bilinmiyor"
# kalıyordu — bölge filtresini boş gösteren sinsi hata.
_KATLAMA = str.maketrans({
    "İ": "I", "I": "I", "ı": "I", "i": "I",
    "Ş": "S", "ş": "S", "Ğ": "G", "ğ": "G",
    "Ü": "U", "ü": "U", "Ö": "O", "ö": "O", "Ç": "C", "ç": "C",
    "Â": "A", "â": "A", "Î": "I", "î": "I", "Û": "U", "û": "U",
})


def _katla(s: str) -> str:
    """Karşılaştırma anahtarı: Türkçe harfleri ASCII'ye indir, boşlukları at."""
    return "".join(ch for ch in s.upper().translate(_KATLAMA) if ch.isalnum())


def _bolge_indeksi() -> dict[str, str]:
    """Katlanmış il adı → bölge. Çakışma olursa import anında patlar."""
    idx: dict[str, str] = {}
    for region, cities in REGIONS.items():
        for city in cities:
            key = _katla(city)
            if key in idx and idx[key] != region:
                raise ValueError(f"Bölge tablosunda çakışma: {city} ({idx[key]} / {region})")
            idx[key] = region
    return idx


_BOLGE_INDEX: dict[str, str] = _bolge_indeksi()


# Kurum adından il çıkarımı için bilinen istisnalar: adında il geçmeyen ama
# ili belli kurumlar. Ölçüm (2026-09-05): ili boş 128 kayıttan 64'ü kurum
# adındaki il adıyla çözülüyor; kalanların çoğu bu tür kurumlar.
KURUM_IL_ISTISNA: dict[str, str] = {
    "KARADENIZ TEKNIK": "TRABZON",
    "ORTA DOGU TEKNIK": "ANKARA",
    "BOGAZICI": "İSTANBUL",
    "EGE UNIVERSITESI": "İZMİR",
    "HACETTEPE": "ANKARA",
    "GAZI UNIVERSITESI": "ANKARA",
    "DOKUZ EYLUL": "İZMİR",
    "ULUDAG": "BURSA",
    "CUKUROVA": "ADANA",
    "ATATURK UNIVERSITESI": "ERZURUM",
    "INONU UNIVERSITESI": "MALATYA",
    "FIRAT UNIVERSITESI": "ELAZIĞ",
    "AKDENIZ UNIVERSITESI": "ANTALYA",
    "ONDOKUZ MAYIS": "SAMSUN",
    "PAMUKKALE": "DENİZLİ",
    "SELCUK UNIVERSITESI": "KONYA",
    "ANADOLU UNIVERSITESI": "ESKİŞEHİR",
    "MARMARA UNIVERSITESI": "İSTANBUL",
    "YILDIZ TEKNIK": "İSTANBUL",
    "GEBZE TEKNIK": "KOCAELİ",
    "TURKIYE SAGLIK ENSTITULERI": "İSTANBUL",
    "KUZEY ANADOLU KALKINMA": "KASTAMONU",
    "INEBOLU": "KASTAMONU",
}


def metinden_il_bul(metin: str | None) -> str | None:
    """Serbest metinde geçen il adını bul (kurum adı, başlık vb.).

    Kamu kaynaklarının çoğu ayrı bir şehir alanı vermiyor; il bilgisi yalnız
    kurum adında geçiyor ("ARDAHAN ÜNİVERSİTESİ" → ARDAHAN). Ölçüm
    (2026-09-05, 128 ilsiz kayıt): kelime taramasıyla 64'ü çözülüyor.

    Önce bilinen istisnalar (adında il geçmeyen kurumlar), sonra kelime
    taraması. Bulunamazsa None.
    """
    if not metin:
        return None
    katlanmis = _katla(metin)
    for anahtar, il in KURUM_IL_ISTISNA.items():
        if _katla(anahtar) in katlanmis:
            return il
    # Kelime bazlı: 2 harften uzun kelimeler, il adıyla birebir eşleşme.
    # Önek eşleme YAPILMAZ — "VAN" birçok kelimeyi yanlış eşleştirirdi.
    for kelime in re.split(r"[\s,/|()\-]+", metin):
        if len(kelime) > 2 and _katla(kelime) in _BOLGE_INDEX:
            return kelime
    return None


def il_ilce_ayikla(konum: str | None) -> tuple[str | None, str | None, str]:
    """Serbest konum metninden (il, ilce, bolge) çıkar.

    İş ilanı kaynakları konumu tek alanda ve **tutarsız sırada** veriyor:
      Jooble    -> "Ankara, Çankaya"   (il, ilçe)
      Careerjet -> "Konak, İzmir"      (ilçe, il)
    Bu yüzden sıraya güvenilmez; hangi parçanın 81 ilden biri olduğuna bakılır.

    Ölçüm (2026-09-05, 487 kayıt): birleşik alan doğrudan `il_to_bolge`'ye
    verildiğinde 336 kayıtta bölge "Bilinmiyor" kalıyordu (%69).

    Dönüş: il bulunamazsa (None, None, "Bilinmiyor"); ilçe yoksa ilce None.
    """
    if not konum:
        return None, None, "Bilinmiyor"

    parcalar = [p.strip() for p in re.split(r"[,/|]", konum) if p.strip()]
    if not parcalar:
        return None, None, "Bilinmiyor"

    il = ilce = None
    # 1) Parçanın tamamı bir il mi? ("Ankara", "İzmir")
    for parca in parcalar:
        if _katla(parca) in _BOLGE_INDEX:
            il = parca
            break
    # 2) Değilse parça içindeki KELİMELERDEN biri il mi?
    #    "İstanbul Avrupa" / "İstanbul Anadolu Yakası" gibi yakalar (66 kayıt).
    #    Kelime bazlı; önek eşleme yapılmaz, yoksa "Van" birçok kelimeyi yanlış
    #    eşleştirirdi.
    kelimeden = False
    if il is None:
        for parca in parcalar:
            for kelime in parca.split():
                if _katla(kelime) in _BOLGE_INDEX:
                    il, kelimeden = kelime, True
                    # İl kelimesi çıkarılınca kalan varsa o ilçe/yaka etiketidir:
                    # "İstanbul Avrupa" -> ilçe "Avrupa" (tüm metin DEĞİL).
                    artik = " ".join(k for k in parca.split() if k != kelime).strip()
                    ilce = artik or None
                    break
            if il:
                break
    if il is None:
        return None, None, "Bilinmiyor"

    if not kelimeden:
        kalan = [p for p in parcalar if p is not il]
        ilce = kalan[0] if kalan else None
    return il, ilce, _BOLGE_INDEX.get(_katla(il), "Bilinmiyor")


def il_to_bolge(il_adi: str | None) -> str:
    """İl adından bölgeyi bul. Bilinmiyorsa 'Bilinmiyor' döner.

    Yazım farklarına dayanıklıdır: "İSTANBUL", "Istanbul", "istanbul",
    " İstanbul " hepsi "Marmara" döner.
    """
    if not il_adi:
        return "Bilinmiyor"
    dogrudan = _BOLGE_INDEX.get(_katla(il_adi))
    if dogrudan:
        return dogrudan
    # Çağıranlar konumu çoğu zaman birleşik veriyor ("Ankara, Çankaya",
    # "Konak, İzmir", "İstanbul Avrupa"). Doğrudan eşleşme tutmazsa ayıklayıcıya
    # düş — yoksa bölge sessizce "Bilinmiyor" kalıyordu (486 kayıtta 339'u).
    return il_ilce_ayikla(il_adi)[2]


# İl kodu → ad (ÖSYM standart kodları)
PLAKA_KODLARI: dict[int, str] = {
    1: "ADANA", 2: "ADIYAMAN", 3: "AFYONKARAHİSAR", 4: "AĞRI", 5: "AMASYA",
    6: "ANKARA", 7: "ANTALYA", 8: "ARTVİN", 9: "AYDIN", 10: "BALIKESİR",
    11: "BİLECİK", 12: "BİNGÖL", 13: "BİTLİS", 14: "BOLU", 15: "BURDUR",
    16: "BURSA", 17: "ÇANAKKALE", 18: "ÇANKIRI", 19: "ÇORUM", 20: "DENİZLİ",
    21: "DİYARBAKIR", 22: "EDİRNE", 23: "ELAZIĞ", 24: "ERZİNCAN", 25: "ERZURUM",
    26: "ESKİŞEHİR", 27: "GAZİANTEP", 28: "GİRESUN", 29: "GÜMÜŞHANE", 30: "HAKKARİ",
    31: "HATAY", 32: "ISPARTA", 33: "MERSİN", 34: "İSTANBUL", 35: "İZMİR",
    36: "KARS", 37: "KASTAMONU", 38: "KAYSERİ", 39: "KIRKLARELİ", 40: "KIRŞEHİR",
    41: "KOCAELİ", 42: "KONYA", 43: "KÜTAHYA", 44: "MALATYA", 45: "MANİSA",
    46: "KAHRAMANMARAŞ", 47: "MARDİN", 48: "MUĞLA", 49: "MUŞ", 50: "NEVŞEHİR",
    51: "NİĞDE", 52: "ORDU", 53: "RİZE", 54: "SAKARYA", 55: "SAMSUN",
    56: "SİİRT", 57: "SİNOP", 58: "SİVAS", 59: "TEKİRDAĞ", 60: "TOKAT",
    61: "TRABZON", 62: "TUNCELİ", 63: "ŞANLIURFA", 64: "UŞAK", 65: "VAN",
    66: "YOZGAT", 67: "ZONGULDAK", 68: "AKSARAY", 69: "BAYBURT", 70: "KARAMAN",
    71: "KIRIKKALE", 72: "BATMAN", 73: "ŞIRNAK", 74: "BARTIN", 75: "ARDAHAN",
    76: "IĞDIR", 77: "YALOVA", 78: "KARABÜK", 79: "KİLİS", 80: "OSMANİYE",
    81: "DÜZCE",
}


# === Sahil / Merkez / Metropol metadata (turkey_geo.json) ===

def _tr_upper(s: str) -> str:
    """Türkçe-güvenli upper (i→İ, ı→I)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


@lru_cache(maxsize=1)
def _load_geo_json() -> dict:
    here = Path(__file__).resolve()
    project_root = here.parents[3]
    geo_path = project_root / "data" / "raw" / "turkey_geo.json"
    with open(geo_path, encoding="utf-8") as f:
        return json.load(f)


def is_coastal_city(city: str | None) -> bool:
    """İl deniz kıyısı mı?"""
    if not city:
        return False
    return _tr_upper(city) in _load_geo_json()["coastal_cities"]


def get_seas(city: str | None) -> list[str]:
    """İlin kıyısı olduğu denizler."""
    if not city:
        return []
    info = _load_geo_json()["coastal_cities"].get(_tr_upper(city))
    return list(info["seas"]) if info else []


def get_coast_km(city: str | None) -> int | None:
    """İlin kıyı uzunluğu (km)."""
    if not city:
        return None
    info = _load_geo_json()["coastal_cities"].get(_tr_upper(city))
    return info.get("coast_km") if info else None


def is_metropolis(city: str | None) -> bool:
    """Büyükşehir mi?"""
    if not city:
        return False
    return _tr_upper(city) in _load_geo_json()["metropolises"]


def is_central_district(city: str | None, district: str | None) -> bool:
    """İlçe şehrin merkez ilçesi mi?

    "MERKEZ" otomatik True. Büyükşehirlerde merkez ilçe listesi `central_districts` içinde.
    """
    if not district:
        return False
    d_upper = _tr_upper(district)
    if d_upper == "MERKEZ":
        return True
    central = _load_geo_json()["central_districts"].get(_tr_upper(city or ""), [])
    return d_upper in central


def geo_summary(city: str | None, district: str | None) -> dict:
    """Tek üniversite/bölüm için coğrafi özet."""
    return {
        "is_coastal": is_coastal_city(city),
        "seas": get_seas(city),
        "coast_km": get_coast_km(city),
        "is_metropolis": is_metropolis(city),
        "is_central_district": is_central_district(city, district),
    }


def cities_by_sea(sea: str) -> list[str]:
    """Belirli bir denize kıyısı olan iller."""
    sea = sea.strip().capitalize()
    return [
        city
        for city, info in _load_geo_json()["coastal_cities"].items()
        if sea in info["seas"]
    ]


def all_coastal_cities() -> list[str]:
    return list(_load_geo_json()["coastal_cities"].keys())


def all_metropolises() -> list[str]:
    return list(_load_geo_json()["metropolises"])
