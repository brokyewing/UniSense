"""Intent router — sorgu analizi, yönlendirme ve context inşa.

ask_service.py'den ayrıldı (ponytail: tek sorumluluk, küçük dosyalar).
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING

from unisense.core.logging import get_logger
from unisense.core.text import fold_tr
from unisense.domain.enums import ScoreType
from unisense.domain.geo import REGIONS

if TYPE_CHECKING:
    from unisense.application.services.recommendation_service import RecommendationService
    from unisense.domain.models import Query

logger = get_logger(__name__)


# === Türkçe-güvenli lowercase ===
def _tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


# === Pattern'ler — sorgudan sıra/puan/uni türü/bölüm çıkar ===

# Sıralama patternleri (büyükten küçüğe spesiflik)
_RANK_PATTERNS = [
    # "300.000 sıra", "1.250.000 sıralama" — noktalı sayıyı TAM yakala (1-2 grup) VE
    # "sıra" bağlamı ZORUNLU. Eski desen bağlamsızdı: "450.512 puan"ı sıra (450512)
    # sanıyor, "1.250.000"da leftmost "1.250"i alıp sırayı 1250 yapıyordu.
    (re.compile(r"\b(\d{1,3}(?:\.\d{3}){1,2})\s*\.?\s*(?:sıra|sıralam)"),
     lambda m: int(m.group(1).replace(".", ""))),
    # "300 bin", "300bin", "100K", "300 k"
    (re.compile(r"\b(\d{1,3})\s*(?:bin|k)\b"),
     lambda m: int(m.group(1)) * 1000),
    # "50000 sıra", "12000 sıralama"
    (re.compile(r"\b(\d{4,7})\s*(?:sıra|sıralam|sıramla)"),
     lambda m: int(m.group(1))),
    # "rank 50000"
    (re.compile(r"\brank[\s:]*(\d{4,7})\b"),
     lambda m: int(m.group(1))),
]

# Puan patternleri
_SCORE_PATTERNS = [
    re.compile(r"\b(\d{3}(?:[.,]\d{1,3})?)\s*puan(?:la|ı|ım)?\b"),
    re.compile(r"\bpuanım[\s:]*(\d{3}(?:[.,]\d{1,3})?)\b"),
]

# Puan türü
_SCORE_TYPE_MAP = {
    "SAY":  [r"\bsay(ı|i)sal\b", r"\bsay\b", r"\bsayisal\b"],
    "EA":   [r"e(ş|s)it\s*a(ğ|g)(ı|i)rl(ı|i)k", r"\bea\b"],
    "SÖZ":  [r"\bs(ö|o)zel\b", r"\bs(ö|o)z\b"],
    "DİL":  [r"yabanc(ı|i)\s*dil", r"\bdil\b"],
    "TYT":  [r"\btyt\b"],
}

# Üniversite türü
_UNI_TYPE_PATTERNS = [
    (re.compile(r"\bdevlet\b"),         "Devlet"),
    (re.compile(r"\bvak(ı|i)f\b"),      "Vakıf"),
    (re.compile(r"\bkktc\b"),           "KKTC"),
    (re.compile(r"\byurt\s*d(ı|i)(ş|s)(ı|i)\b"), "YURTDISI"),
]

# Trend / yıllar arası sorgu pattern'i
_TREND_PATTERNS = [
    re.compile(r"\btrend"),
    re.compile(r"\b(y(ı|i)l|y(ı|i)llar)\s+(i(ç|c)inde|aras(ı|i))"),
    re.compile(r"\bge(ç|c)mi(ş|s)"),
    re.compile(r"\b(20\d\d)\s*[-–]\s*(20\d\d)"),  # "2020-2024"
    re.compile(r"y(ü|u)kseli|d(ü|u)(ş|s)(ü|u)"),  # "yükseliş/düşüş"
    re.compile(r"\bson\s+\d+\s+y(ı|i)l"),
]

# Coğrafi filtreler — Türkçe ekler için sondan \b kaldırıldı (prefix-match)
_GEO_PATTERNS = [
    # deniz, denizi, denizin, denize, sahili, kıyısında
    (re.compile(r"\b(deniz|sahil|k(ı|i)y(ı|i))"),                       "coastal"),
    # içerideki, içerde, iç kesim, kara
    (re.compile(r"\b(i(ç|c)\s*kesim|i(ç|c)er(de|ide)|kara\s*l)"),         "inland"),
    # merkez, merkezi, merkezindeki, şehir merkezi
    (re.compile(r"\b(merkez|(ş|s)ehir\s*merkezi)"),                       "central"),
    # metropol, metropolün, büyük şehir, büyükşehir
    (re.compile(r"\b(metropol|b(ü|u)y(ü|u)k\s*(ş|s)ehir)"),               "metropolis"),
    # karadeniz, karadenize, karadeniz'in
    (re.compile(r"\bkaradeniz"),                                          "sea_karadeniz"),
    (re.compile(r"\bmarmara"),                                            "sea_marmara"),
    (re.compile(r"\bege\b"),                                              "sea_ege"),
    (re.compile(r"\bakdeniz"),                                            "sea_akdeniz"),
    (re.compile(r"\bbo(ğ|g)az\s*manzara"),                                "sea_marmara"),
]

# Şehir adından sonra gelebilecek ekler (fold'lu). Serbest önek eşleşmesi
# TUZAK: "bölüm"→"bolum" BOLU'yu, "karşı"→"karsi" KARS'ı yakalıyordu.
# Orijinaldeki iç içe grup parantezi dengesizdi — tek grup içinde hepsini topladık.
_CITY_SUFFIX = r"(?:'?(?:da|de|ta|te|dan|den|tan|ten|daki|deki|taki|teki|ya|ye|yi|yu|nin|nun|un|in|la|le|sinda|sinde))?\b"


# 81 il — sorgudan şehir tespiti için (geo.REGIONS'tan düzleştirilmiş)
@lru_cache(maxsize=1)
def _city_patterns() -> list[tuple[re.Pattern[str], str]]:
    pats = []
    for cities in REGIONS.values():
        for city in cities:
            low = fold_tr(city)
            pats.append((re.compile(rf"\b{re.escape(low)}{_CITY_SUFFIX}"), city))
    return pats


# "X bölümü NEREDE/HANGİ üniversitede var?" kalıpları
_WHERE_PATTERNS = [
    re.compile(r"hangi\s+(ü|u)niversite"),
    re.compile(r"\bnerede\b|\bnerelerde\b|\bhangi\s+(ş|s)ehir"),
    re.compile(r"\bnereler(i|e)?\b"),
    re.compile(r"\bvar\s*m(ı|i)\b"),
    re.compile(r"\bbulunan\b|\bbulunuyor\b|\ba(ç|c)an\b"),
    re.compile(r"\blistele\b|\bt(ü|u)m(ü|u)n(ü|u)\b"),
]

# Sayım/envanter soruları
_COUNT_RE = re.compile(
    r"ka(ç|c)\s*(tane|adet|program|b(ö|o)l(ü|u)m|(ü|u)niversite|kod)|"
    r"toplam\s+ka(ç|c)|say(ı|i)s(ı|i)\s+(ka(ç|c)|nedir|ne)", re.IGNORECASE)

# "24 tane tercih yap" / "tercih listesi oluştur"
_TERCIH_N_RE = re.compile(r"(\d{1,2})\s*(?:tane|adet)?\s*tercih", re.IGNORECASE)
_TERCIH_LIST_RE = re.compile(
    r"tercih\s*(listesi|yap|olu(ş|s)tur|haz(ı|i)rla|ver|et)", re.IGNORECASE)

# "kaç net yapmalıyım"
_NET_RE = re.compile(
    r"\bka(ç|c)\s*net\b|\bnet\s*(yap|gerek|laz(ı|i)m|olmal|yeter|at(ı|i)|istiyor)",
    re.IGNORECASE)

# Takip (refinement) mesajı işaretleri
_FOLLOWUP_RE = re.compile(
    r"\b(t(ü|u)m(ü|u)?|hepsi(ni)?|b(ü|u)t(ü|u)n|di(ğ|g)er(ler(i|ini)?)?|ba(ş|s)ka|"
    r"peki|bunlar(dan|ı)?|hangi(leri|si)?|ayn(ı|i)|(ş|s)ehir|il(ç|c)e|iller|"
    r"o zaman|bi(r)?\s*de|de\s*bak|da\s*bak|nas(ı|i)l)\b", re.IGNORECASE)

# Kullanıcı KENDİ puanını kastediyor mu
_SELF_SCORE_RE = re.compile(
    r"puan(ı|i)m|s(ı|i)ra(la)?m|kazan(abil|(ı|i)r\s*m)|gir(er|ebilir)\s*m|"
    r"yeter\s*m|tutar\s*m|yazabil|(ş|s)ans(ı|i)m|nereye\s*gir|benim\s*puan", re.IGNORECASE)

# OBP / diploma notu
_OBP_RE = re.compile(r"\bobp[^\d]{0,6}(\d{2,3}(?:[.,]\d+)?)", re.IGNORECASE)
_DIPLOMA_RE = re.compile(
    r"(?:diploma|ortalama|not\s*ortalam\w*)[^\d]{0,12}(\d{1,3}(?:[.,]\d+)?)", re.IGNORECASE)


@lru_cache(maxsize=1)
def _group_token_index() -> dict[str, list[str]]:
    """Bölüm grubu adlarının ayırt edici token index'i (fold'lu)."""
    from unisense.application.services.compass_taxonomy import get_taxonomy

    tok_to_groups: dict[str, set[str]] = {}
    for g in get_taxonomy()["departments"]:
        for t in re.findall(r"[a-zçğıöşü]+", fold_tr(g["name"])):
            if len(t) >= 4 and t not in {
                "bilim", "bilimleri", "yonetimi", "sanatlari", "bilgi",
                "genel", "temel", "uygulamali", "hizmetleri", "sistemleri",
                "teknolojisi", "teknolojileri", "tasarimi",
            }:
                tok_to_groups.setdefault(t, set()).add(g["name"])
    return {t: sorted(gs) for t, gs in tok_to_groups.items() if len(gs) <= 8}


# Yaygın bölüm anahtar kelimeleri
_DEPT_KEYWORDS = [
    "tıp", "diş", "eczacılık", "hemşirelik", "fizyoterapi", "veteriner",
    "bilgisayar mühendis", "yazılım mühendis", "yapay zeka", "veri bilim",
    "elektrik", "elektronik", "makine", "endüstri mühendis", "inşaat",
    "kimya mühendis", "biyomedikal", "havacılık", "uçak", "uzay", "otomotiv",
    "mimarlık", "iç mimarlık", "tasarım",
    "hukuk", "psikoloji", "sosyoloji", "felsefe",
    "iktisat", "işletme", "maliye", "muhasebe", "bankacılık", "pazarlama",
    "öğretmenlik", "eğitim",
    "matematik", "fizik", "biyoloji",
    "gazetecilik", "halkla ilişkiler", "iletişim",
    "ilahiyat",
]


def _extract_intent(query: str) -> dict | None:
    """Sorgudan sıra/puan/şehir/üni/bölüm intent'i çıkar.

    Return:
        None  → yapılandırılmış veri gerektirmeyen sorgu (saf RAG kullan)
        dict  → {rank?, score?, score_type, uni_types, departments,
                 cities, universities, geo_flags, is_count, is_net, obp_katki, list_n}
    """
    q = _tr_lower(query)

    # Sıralama
    rank = None
    for pat, fn in _RANK_PATTERNS:
        m = pat.search(q)
        if m:
            try:
                rank = fn(m)
                break
            except (ValueError, IndexError):
                pass

    # Puan
    score = None
    for pat in _SCORE_PATTERNS:
        m = pat.search(q)
        if m:
            try:
                score = float(m.group(1).replace(",", "."))
                if not (100 <= score <= 600):
                    score = None
                break
            except (ValueError, IndexError):
                pass

    # Coğrafi flagler
    geo_flags: list[str] = []
    for pat, label in _GEO_PATTERNS:
        if pat.search(q):
            geo_flags.append(label)

    # Şehir + bölüm eşleşmeleri fold'lu
    qf = fold_tr(query)

    global _CITY_PATTERNS
    if _CITY_PATTERNS is None:
        _CITY_PATTERNS = _city_patterns()
    cities: list[str] = []
    for pat, city in _CITY_PATTERNS:
        if pat.search(qf):
            cities.append(city)

    # Bölüm anahtar kelimeleri
    departments: list[str] = []
    for kw in _DEPT_KEYWORDS:
        if re.search(rf"(?<![a-z]){re.escape(fold_tr(kw))}", qf):
            departments.append(kw)

    # Taksonomi-tabanlı bölüm tespiti
    token_index = _group_token_index()
    q_words = set(re.findall(r"[a-zçğıöşü]+", qf))
    for w in q_words:
        if w in token_index and w not in [fold_tr(k) for k in departments]:
            departments.append(w)

    is_where_query = any(p.search(q) or p.search(qf) for p in _WHERE_PATTERNS)
    is_count = bool(_COUNT_RE.search(q))
    is_net = bool(_NET_RE.search(q))
    obp_katki = _parse_obp_katki(q) if is_net else None

    list_n = None
    m_n = _TERCIH_N_RE.search(q)
    if m_n:
        try:
            n = int(m_n.group(1))
            if 2 <= n <= 30:
                list_n = n
        except ValueError:
            pass
    is_tercih_list = list_n is not None or bool(_TERCIH_LIST_RE.search(q))

    # Üniversite adları
    universities: list[str] = []
    try:
        from unisense.application.services.recommendation_service import detect_universities
        universities = detect_universities(query)
    except Exception:
        pass

    has_listing_target = departments and (
        cities or universities or is_where_query or is_count or is_tercih_list or is_net)
    if rank is None and score is None and not geo_flags and not has_listing_target:
        return None

    # Puan türü
    score_type = "SAY"
    for st, pats in _SCORE_TYPE_MAP.items():
        if any(re.search(p, q) for p in pats):
            score_type = st
            break

    # Üniversite türü
    uni_types: list[str] = []
    for pat, label in _UNI_TYPE_PATTERNS:
        if pat.search(q):
            uni_types.append(label)

    return {
        "rank": rank,
        "score": score,
        "score_type": score_type,
        "uni_types": uni_types,
        "departments": departments,
        "cities": cities,
        "universities": universities,
        "geo_flags": geo_flags,
        "is_count": is_count,
        "is_net": is_net,
        "obp_katki": obp_katki,
        "list_n": list_n,
    }


_CITY_PATTERNS: list[tuple[re.Pattern[str], str]] | None = None


def _is_refinement(text: str) -> bool:
    """Kısa + takip-işareti taşıyan (kendi konusunu kurmayan) mesaj mı."""
    return len(re.findall(r"\w+", text)) <= 6 and bool(_FOLLOWUP_RE.search(text))


def _routing_text(query: Query) -> str:
    """Yapısal yönlendirme için bağlamsal metin: kısa TAKİP mesajlarında önceki
    kullanıcı mesajlarını da kat (chat bağlam sürekliliği, çok-turlu)."""
    cur = query.text
    hist = getattr(query, "history", None) or []
    if not _is_refinement(cur):
        return cur
    users = [t.text for t in hist if getattr(t, "role", None) == "user" and t.text]
    if not users:
        return cur
    collected: list[str] = []
    for txt in reversed(users[-6:]):
        collected.append(txt)
        if not _is_refinement(txt):
            break
    collected.reverse()
    return "\n".join([*collected, cur])


@lru_cache(maxsize=1)
def _rankings_year() -> int:
    """Rankings verisinin yılı — LLM'e giden 'X verisi' etiketleri veriden türesin."""
    try:
        from unisense.application.services.recommendation_service import _load_data
        rankings, _, _ = _load_data()
        years = {r.get("year") for r in rankings[:500] if r.get("year")}
        return max(years) if years else 2025
    except Exception:
        return 2025


# === YKS net tahmini (TERSİNE: taban puanı → yaklaşık net) ===
_OBP_KATKI = 50.0
_TYT_SORU = 120
_AYT_SORU = 80


def _parse_obp_katki(q: str) -> float | None:
    m = _OBP_RE.search(q)
    if m:
        obp = float(m.group(1).replace(",", "."))
        if 0 <= obp <= 500:
            return round(obp * 0.12, 1)
    m = _DIPLOMA_RE.search(q)
    if m:
        nota = float(m.group(1).replace(",", "."))
        if 0 <= nota <= 100:
            return round(nota * 5 * 0.12, 1)
    return None


def _estimate_nets(score: float | None, score_type: str, obp_katki: float | None = None) -> dict | None:
    if not score:
        return None
    katki = obp_katki if obp_katki is not None else _OBP_KATKI
    if score_type == "TYT":
        f = max(0.0, min(1.0, (score - 100 - katki) / 400))
        return {"tyt": round(f * _TYT_SORU), "ayt": None}
    f = max(0.0, min(1.0, (score - 100 - katki) / 400))
    return {"tyt": round(f * _TYT_SORU), "ayt": round(f * _AYT_SORU)}


def _detect_city_in_query(qf: str) -> str | None:
    global _CITY_PATTERNS
    if _CITY_PATTERNS is None:
        _CITY_PATTERNS = _city_patterns()
    for pat, city in _CITY_PATTERNS:
        if pat.search(qf):
            return city
    return None


def _detect_bolum_in_query(query: str) -> str:
    qf = fold_tr(query)
    best = ""
    for kw in _DEPT_KEYWORDS:
        if fold_tr(kw) in qf and len(kw) > len(best):
            best = kw
    if best:
        return best
    token_index = _group_token_index()
    words = re.findall(r"[a-zçğıöşü]+", qf)
    for w in words:
        if w in token_index:
            return w
    city = _detect_city_in_query(qf)
    city_fold = fold_tr(city) if city else ""
    for w in words:
        if len(w) >= 4 and w not in _BOLUM_STOPWORDS and w != city_fold:
            return w
    return ""


_BOLUM_STOPWORDS = frozenset({
    "kpss", "dgs", "puan", "puanla", "puani", "puanim", "puanimla",
    "kadro", "kadrosu", "kadrolar", "kadrolari", "kadroya", "kadrolara",
    "memur", "memurluk", "memuriyet", "atama", "atanabilir", "atanma",
    "hangi", "nasil", "neler", "nedir", "olabilir", "olabilirmiyim",
    "basvur", "basvuru", "basvurabilir", "basvurabilirim", "basvurabilirmiyim",
    "mezun", "mezunu", "mezunuyum", "mezunum", "bolum", "bolumu", "bolumunden",
    "gecebilir", "gecebilirmiyim", "gecis", "lisans", "onlisans", "ortaogretim",
    "program", "programlar", "programa", "tercih", "olur", "yapabilir",
    "calisabilir", "var", "yok", "gibi", "icin", "ile", "benim", "bana",
    "sonra", "once", "simdi", "yerlesebilir", "yerlesirmiyim", "istiyorum",
    "toplam", "kontenjan", "kisilik", "kisi", "kac", "adet", "acildi",
    "acilan", "acik", "kadar", "sayisi", "donem", "genel", "hepsi", "tum",
})


_KPSS_RE = re.compile(r"\bkpss\b|\bmemur(lug|luk|iyet|u|a)?\b|\batan(ma|abilir|(ı|i)r(ı|i)m)", re.IGNORECASE)
_GENERIC_PLACEMENT_RE = re.compile(
    r"nereye\s+(girebilir|yerle(ş|s))|hangi\s+(b(ö|o)l(ü|u)m|program|kadro)|"
    r"\byerle(ş|s)(ebilir|irim|me)\b|puan(ı|i)mla", re.IGNORECASE)
_DGS_RE = re.compile(
    r"\bdgs\b|dikey\s*ge(ç|c)i(ş|s)|"
    r"(ö|o)n\s*lisans.*(lisans|ge(ç|c))|lisansa\s+ge(ç|c)", re.IGNORECASE)
_KPSS_PUAN_RE = re.compile(r"\b(\d{2,3}(?:[.,]\d{1,3})?)\s*(?:kpss\s*)?puan")
_KPSS_AGG_RE = re.compile(
    r"topla(m|mda)|ka(ç|c)\s*(ki(ş|s)i|kadro|kontenjan|adet|memur)|"
    r"ka(ç|c)\s*ki(ş|s)ilik|kontenjan|ka(ç|c)\s*al(ı|i)m", re.IGNORECASE)


def _estimate_kpss_net(puan: float | None) -> int | None:
    if not puan:
        return None
    return max(0, min(120, round(2 * (puan - 40))))


def _build_kpss_context(query: str, user_context: dict | None = None) -> str:
    from unisense.core.di import get_kpss_service
    from unisense.core.text import fold_tr

    uc = user_context or {}
    qf = fold_tr(query)
    is_net = bool(_NET_RE.search(qf))
    puan = uc.get("kpss_puan")
    m = _KPSS_PUAN_RE.search(qf)
    if m:
        v = float(m.group(1).replace(",", "."))
        if 40 <= v <= 105:
            puan = v
    is_agg = bool(_KPSS_AGG_RE.search(qf))
    bolum = "" if is_agg else _detect_bolum_in_query(query)
    il = _detect_city_in_query(qf)
    duzey = ("önlisans" if "onlisans" in qf or "on lisans" in qf
             else "ortaöğretim" if "ortaogretim" in qf or "lise" in qf
             else uc.get("kpss_duzey") or "lisans")

    r = get_kpss_service().kadro_ara(bolum=bolum, puan=puan, duzey=duzey, il=il, limit=15)
    donem = r.get("donem", "2026/1")
    ozet = get_kpss_service().donem_ozeti()
    dz = ozet["duzeyler"]
    dz_str = ", ".join(f"{d} {v['kadro']} kadro/{v['kontenjan']} kişi" for d, v in dz.items())
    lines = [f"=== KPSS {donem} MERKEZİ YERLEŞTİRME (B GRUBU) KADROLARI ===",
             (f"DÖNEM GENELİ: toplam {ozet['toplam_kadro']} kadro, "
              f"{ozet['toplam_kontenjan']} kişilik kontenjan "
              f"({ozet['kurum_sayisi']} kurum, {ozet['il_sayisi']} il). "
              f"Düzey kırılımı: {dz_str}."),
             (f"Filtre: düzey={duzey}, bölüm={bolum or 'tümü'}, "
              f"il={il or 'tümü'}, puan={puan or '?'}"),
             (f"Bu filtreye uyan: {r['total']} kadro / "
              f"{r.get('toplam_kontenjan', 0)} kişilik (ilk 15 örnek)"), ""]
    if re.search(r"(ö|o)(ğ|g)retmen", qf):
        lines.insert(1, "⚠ DİKKAT: Öğretmenlik ataması sorulmuş olabilir. Öğretmen "
                        "atamaları KPSS-ÖABT ile MEB üzerinden yapılır ve AŞAĞIDAKİ "
                        "listede YER ALMAZ. Aşağıdakiler ilgili alandan mezunların "
                        "başvurabileceği B grubu memur kadrolarıdır (öğretmenlik değil).")
    if is_net:
        hedef = f" '{puan}' KPSS puanına ulaşmak için ~{_estimate_kpss_net(puan)}/120 net gerekir." if puan else ""
        lines.append(
            "YÖNERGE: Kullanıcı KAÇ NET sordu. Kadroların yanındaki '~net' TAHMİNÎ "
            "değeri kullan (KPSS puanı ≈ 40 + 0.5×net; GY+GK toplam 120 soru)." + hedef
            + " MUTLAKA belirt: tahminîdir, soru zorluğu ve aday ortalamasına göre "
            "değişir; kesin hesap için Hesap sayfası (net gir → puan gör).")
    for it in r["items"]:
        taban = f"geçen dönem taban {it['gecmis_taban']:.2f}" if it["gecmis_taban"] else "geçmiş taban yok"
        kosul = " ⚠ ÖZEL KOŞUL VAR" if it.get("ozel_kosullar") else ""
        net_s = ""
        if is_net and it.get("gecmis_taban"):
            n = _estimate_kpss_net(it["gecmis_taban"])
            if n is not None:
                net_s = f" | ~net: {n}/120"
        lines.append(f"• [{it['kadro_kodu']}] {it['unvan']} — {it['kurum']} ({it['il']}) "
                     f"kontenjan {it['kontenjan']}, {taban}, {it['eslesme']}{kosul}{net_s}")
    lines.append("")
    lines.append("NOT: B grubu merkezi yerleştirme kadroları. A grubu (uzman yrd/müfettiş) "
                 "kurum sınavlarıyla, ÖĞRETMEN atamaları ise KPSS-ÖABT ile MEB üzerinden "
                 "yapılır — ikisi de bu listede OLMAZ; kullanıcı öğretmenlik soruyorsa bunu "
                 "açıkça belirt. ⚠ işaretli kadroların yaş/YDS/sertifika gibi özel koşulları "
                 "var — kılavuzdan kontrol edilmeli. " + r["uyari"])
    return "\n".join(lines)


def _build_dgs_context(query: str, user_context: dict | None = None) -> str:
    from unisense.core.di import get_dgs_service
    from unisense.core.text import fold_tr

    uc = user_context or {}
    qf = fold_tr(query)
    puan = uc.get("dgs_puan")
    mp = re.search(r"\b(\d{3}(?:[.,]\d{1,3})?)\s*puan", qf)
    if mp:
        v = float(mp.group(1).replace(",", "."))
        if 140 <= v <= 500:
            puan = v
    pt = ("EA" if re.search(r"\bea\b|esit", qf)
          else "SÖZ" if re.search(r"\bsoz(el)?\b", qf)
          else "SAY" if re.search(r"\bsay(isal)?\b", qf)
          else uc.get("dgs_turu") or "SAY")
    bolum = _detect_bolum_in_query(query)
    il = _detect_city_in_query(qf)

    r = get_dgs_service().program_ara(puan_turu=pt, puan=puan, bolum=bolum, il=il, limit=15)
    lines = [f"=== DGS LİSANS GEÇİŞ PROGRAMLARI ({r.get('yil', _rankings_year())} tabanları) ===",
             (f"Filtre: puan türü={pt}, puan={puan or '?'}, "
              f"bölüm={bolum or 'tümü'}, il={il or 'tümü'}"),
             f"Uyan program sayısı: {r['total']} (ilk 15)", ""]
    for it in r["items"]:
        taban = f"taban {it['min_puan']:.2f}" if it["min_puan"] else "geçen yıl boş"
        lines.append(f"• [{it['department_code']}] {it['program_adi']} ({it['city']}) "
                     f"— {taban}, kontenjan {it['kontenjan']}")
    lines.append("")
    lines.append(r["uyari"])
    return "\n".join(lines)


def _build_listing_context(intent: dict, rec_service: RecommendationService) -> str:
    list_n = intent.get("list_n")
    result = rec_service.list_programs(
        cities=intent.get("cities") or None,
        uni_codes=intent.get("universities") or None,
        dept_keywords=intent.get("departments") or None,
        limit=max(30, (list_n or 0) + 6),
    )
    if not result["total"]:
        return ""

    scope = []
    if intent.get("cities"):
        scope.append("/".join(intent["cities"]))
    if intent.get("universities"):
        scope.append(f"{len(intent['universities'])} üniversite")
    scope.append(", ".join(intent.get("departments") or []))

    lines = [f"=== PROGRAM LİSTESİ ({' — '.join(s for s in scope if s)}) — {_rankings_year()} verisi ==="]
    lines.append(
        f"Toplam {result['total']} program, toplam kontenjan {result['total_quota']:,}. "
        f"(İlk {len(result['programs'])} tanesi taban sırasına göre listelendi)"
    )
    if intent.get("is_count"):
        lines.append(
            f"YÖNERGE: Kullanıcı SAYIM sordu — net cevap ver: elimizde bu bölüm için "
            f"toplam {result['total']} program var. Ardından birkaç örnek göster."
        )
    us = intent.get("user_score")
    if us:
        ust = intent.get("user_score_type") or "SAY"
        usr = intent.get("user_rank")
        lines.append(
            f"KULLANICI PROFİL PUANI: {us} ({ust})"
            + (f", tahmini sıra ~{usr:,}" if usr else "")
        )
        lines.append(
            "YÖNERGE: Kullanıcı KENDİ puanıyla yerleşip yerleşemeyeceğini soruyor. "
            "Yukarıdaki her programın TABANIYLA kullanıcının puanını/sırasını kıyasla ve "
            "NET değerlendir: puan tabandan belirgin YÜKSEKSE 'rahatça yerleşirsin', "
            "YAKINSA (±birkaç puan) 'sınırda/riskli', DÜŞÜKSE 'bu puanla zor' de. "
            "Örn: '430 puanınla taban 437 olan Çukurova sınırın hafif altında — zor ama "
            "taban düşerse şansın olabilir'. TAHMİNÎdir; kesin sıra sınav sonucuna bağlı, "
            "geçen yıl tabanı bu yıl değişebilir — bunu da belirt."
        )
    if intent.get("is_net"):
        obp_k = intent.get("obp_katki")
        if obp_k is not None:
            obp_not = (
                f"Kullanıcı OBP/diploma verdi (yerleştirmeye ~{obp_k:.0f} puan katkı) — "
                f"'~net' değerleri BU DEĞERE göre hesaplandı. "
            )
        else:
            obp_not = (
                "'~net' değerleri VARSAYILAN OBP (diploma ~85 / ~50 puan katkı) ile "
                "hesaplandı; kullanıcı diploma notunu/OBP'sini yazarsa daha isabetli olur — "
                "bunu nazikçe hatırlat. "
            )
        lines.append(
            "YÖNERGE: Kullanıcı KAÇ NET gerektiğini sordu. Her programın yanındaki '~net' "
            f"TAHMİNÎ değerini kullan (TYT-AYT'de dengeli-eşit başarı varsayımıyla). {obp_not}"
            "En zor ve daha ulaşılabilir programlar için bir net ARALIĞI ver. MUTLAKA belirt: "
            "bu TAHMİNÎDİR, gerçek net dağılıma göre de değişir; kesin hesap için Hesap "
            "sayfasını (net gir → puan gör) öner."
        )
    if list_n:
        lines.append(
            f"YÖNERGE: Kullanıcı {list_n} tercihlik liste istedi ama PUAN/SIRA VERMEDİ. "
            f"Aşağıdaki verilerden {list_n} maddelik NUMARALI liste üret (taban sırasına göre, "
            f"[kod] bölüm — üniversite (şehir) sıra/taban formatında). Listenin kişiselleştirilmiş "
            f"OLMADIĞINI, puanını/sıralamasını yazarsa ya da Tercih sayfasını (/oneriler) "
            f"kullanırsa puanına göre güvenli/hedef/riskli dengesiyle kurulacağını belirt."
        )
    for p in result["programs"]:
        rank_s = f"{p['base_rank']:,}" if p["base_rank"] else "?"
        score_s = f"{p['base_score']:.2f}" if p["base_score"] else "?"
        burs = ""
        if p.get("scholarship") and p["scholarship"] not in p["department_name"]:
            burs = f" ({p['scholarship']})"
        uni = p["university_name"]
        city = "" if p["city"] and p["city"] in uni else f" ({p['city']})"
        net_s = ""
        if intent.get("is_net"):
            est = _estimate_nets(
                p["base_score"], intent.get("score_type", "SAY"),
                intent.get("obp_katki"))
            if est:
                net_s = (f" | ~net: TYT {est['tyt']}"
                         + (f"+AYT {est['ayt']}" if est["ayt"] is not None else ""))
        kars_s = ""
        us = intent.get("user_score")
        if us and p["base_score"]:
            fark = us - p["base_score"]
            if fark >= 12:
                kars_s = f" → SENİN İÇİN GÜVENLİ (puanın {us} tabandan {fark:+.0f})"
            elif fark >= -6:
                kars_s = f" → SENİN İÇİN SINIRDA/RİSKLİ (puanın {us} ≈ taban {p['base_score']:.0f})"
            else:
                kars_s = f" → SENİN İÇİN ZOR (puanın {us} tabandan {fark:.0f} geride)"
        lines.append(
            f"• [{p['department_code']}] {p['department_name']}{burs} — {uni}{city} "
            f"sıra: {rank_s} | taban: {score_s} | kontenjan: {p['quota'] or '?'}{net_s}{kars_s}"
        )
    return "\n".join(lines)


def _build_recommendation_context(intent: dict, rec_service: RecommendationService) -> str:
    if intent.get("rank") is None and intent.get("score") is None:
        listing = _build_listing_context(intent, rec_service)
        if listing:
            return listing

    try:
        st_enum = ScoreType(intent["score_type"]) if isinstance(intent["score_type"], str) else intent["score_type"]
    except ValueError:
        st_enum = ScoreType.SAY

    from unisense.domain.models import StudentProfile
    profile = StudentProfile(
        score_type=st_enum,
        score=intent.get("score"),
        rank=intent.get("rank"),
        preferred_cities=intent.get("cities") or [],
        preferred_uni_types=intent.get("uni_types") or [],
        preferred_departments=intent.get("departments") or [],
    )
    geo_flags = intent.get("geo_flags") or []
    profile._geo_flags = geo_flags
    result = rec_service.recommend(profile)

    lines = [f"=== TERCİH ÖNERİLERİ (sıra bazlı, taban verisi {_rankings_year()}) ==="]
    lines.append(f"Profil: {st_enum.value}, sıra={intent.get('rank') or '?'}, puan={intent.get('score') or '?'}")
    if intent.get("uni_types"):
        lines.append(f"Filtre: {', '.join(intent['uni_types'])}")
    if intent.get("departments"):
        lines.append(f"Bölüm: {', '.join(intent['departments'])}")
    if geo_flags:
        lines.append(f"Coğrafi filtre: {', '.join(geo_flags)}")
    lines.append(f"Notes: {result.notes}")
    list_n = intent.get("list_n")
    if list_n:
        lines.append(
            f"YÖNERGE: Kullanıcı {list_n} tercihlik liste istedi — kovalardan dengeli seç "
            f"(üstte birkaç ÜST SEVİYE, ortada HEDEF ağırlıklı, altta GÜVENLİ) ve tercih "
            f"sırasına dizilmiş NUMARALI {list_n} maddelik TEK liste üret; her maddede "
            f"[kod] bölüm — üniversite (şehir) sıra/taban yaz."
        )
    lines.append("")

    _s, _t, _r = (list_n, list_n, list_n) if list_n else (8, 10, 5)
    for cat_name, cat_list in [
        ("GÜVENLİ (rahat yerleşir)", result.safe[:_s]),
        ("HEDEF (uygun)", result.target[:_t]),
        ("ÜST SEVİYE (zorlama)", result.reach[:_r]),
    ]:
        if not cat_list:
            continue
        lines.append(f"--- {cat_name} ---")
        for r in cat_list:
            rank_s = f"{r.last_year_base_rank:,}" if r.last_year_base_rank else "?"
            score_s = f"{r.last_year_base_score:.2f}" if r.last_year_base_score else "?"
            lines.append(
                f"• [{r.department_code}] {r.department_name} — {r.university_name} ({r.city}) "
                f"sıra: {rank_s} | taban: {score_s}"
            )
        lines.append("")

    return "\n".join(lines)


def _build_profile_context(uc: dict | None) -> str:
    if not uc:
        return ""
    rows: list[str] = []
    yks_p = uc.get("yks_puan")
    if yks_p:
        tur = uc.get("yks_turu") or "SAY"
        sira = uc.get("yks_sira")
        if not sira:
            try:
                from unisense.application.services.recommendation_service import tahmini_sira
                est = tahmini_sira(float(yks_p), tur)
                sira = est["tahmini_sira"] if est else None
            except Exception:
                sira = None
        rows.append(f"YKS: {yks_p} puan ({tur})"
                    + (f", ~{sira:,}. başarı sırası" if sira else ""))
    if uc.get("kpss_puan"):
        rows.append(f"KPSS: {uc['kpss_puan']} puan"
                    + (f" ({uc['kpss_duzey']})" if uc.get("kpss_duzey") else ""))
    if uc.get("dgs_puan"):
        rows.append(f"DGS: {uc['dgs_puan']} puan"
                    + (f" ({uc['dgs_turu']})" if uc.get("dgs_turu") else ""))
    if uc.get("tus_puan"):
        rows.append(f"TUS: {uc['tus_puan']} puan")
    if uc.get("dus_puan"):
        rows.append(f"DUS: {uc['dus_puan']} puan")
    if uc.get("lgs_yuzdelik") is not None:
        rows.append(f"LGS: %{uc['lgs_yuzdelik']} yüzdelik dilim")
    if uc.get("ags_net") is not None:
        rows.append(f"AGS: {uc['ags_net']} net")
    if uc.get("tercih_sehirler"):
        rows.append(f"Tercih ettiği şehirler: {', '.join(uc['tercih_sehirler'])}")
    if uc.get("tercih_uni_turu") and uc.get("tercih_uni_turu") != "all":
        rows.append(f"Üniversite tercihi: {uc['tercih_uni_turu']}")
    kalan = uc.get("calisma_kalan_konu")
    toplam = uc.get("calisma_toplam_konu")
    if kalan is not None and toplam:
        bitti = max(0, toplam - kalan)
        rows.append(f"Çalışma ilerlemesi: {toplam} konudan {bitti} işaretlendi, {kalan} konu kaldı")
    elif kalan is not None:
        rows.append(f"Çalışılacak {kalan} konu kaldı")
    zayif = uc.get("calisma_zayif")
    if zayif:
        rows.append("Zayıf/eksik konular: " + ", ".join(str(z)[:40] for z in zayif[:6]))
    if not rows:
        return ""
    return (
        "=== KULLANICI SINAV PROFİLİ (bu kişinin KENDİ kayıtlı verisi) ===\n"
        + "\n".join(f"- {r}" for r in rows)
        + "\nYÖNERGE: Bu, kullanıcının profilinden SANA verilen KENDİ verisidir. "
        "'puanım/sıralamam/kazanabilir miyim' gibi ifadelerde bunu DOĞRUDAN kullan. "
        "ASLA 'kişisel verine erişemem' deme — erişimin var, yukarıda listeli. Sıra "
        "sorulursa yukarıdaki TEK sırayı kullan (farklı sıra uydurma, tutarlı ol). "
        "Çalışma planı/program istenirse (ör. 'X günde tüm konular', 'günde N soru') "
        "yukarıdaki kalan konu sayısı ve zayıf konuları temel al; gerçekçi günlük "
        "dağılım öner ve Planım sekmesinden otomatik plan kurabileceğini hatırlat."
    )


# === KVPS/DGS sorgu yönlendirmesi için export edilen pattern'ler ===
__all__ = [
    "DGS_RE",
    "GENERIC_PLACEMENT_RE",
    "KPSS_AGG_RE",
    "KPSS_RE",
    "SELF_SCORE_RE",
    "build_dgs_context",
    "build_kpss_context",
    "build_listing_context",
    "build_profile_context",
    "build_recommendation_context",
    "estimate_nets",
    "extract_intent",
    "is_refinement",
    "rankings_year",
    "routing_text",
]

# Public API (snake_case)
extract_intent = _extract_intent
routing_text = _routing_text
is_refinement = _is_refinement
build_kpss_context = _build_kpss_context
build_dgs_context = _build_dgs_context
build_recommendation_context = _build_recommendation_context
build_listing_context = _build_listing_context
build_profile_context = _build_profile_context
estimate_nets = _estimate_nets
rankings_year = _rankings_year

# Pattern'ler (diğer modüller kullanabilir)
KPSS_RE = _KPSS_RE
DGS_RE = _DGS_RE
GENERIC_PLACEMENT_RE = _GENERIC_PLACEMENT_RE
KPSS_AGG_RE = _KPSS_AGG_RE
SELF_SCORE_RE = _SELF_SCORE_RE