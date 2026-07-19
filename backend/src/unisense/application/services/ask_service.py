"""Ask service — RAG sorgu orkestrasyonu + sıra/puan intent routing."""
from __future__ import annotations

import hashlib
import re
import time
from functools import lru_cache
from typing import TYPE_CHECKING

from cachetools import TTLCache

from unisense.application.interfaces.llm_provider import LLMProvider
from unisense.application.services.retrieval_service import RetrievalService
from unisense.application.services.trend_service import has_history, trend_summary
from unisense.core.logging import get_logger
from unisense.domain.enums import ScoreType
from unisense.domain.models import Answer, Query, StudentProfile

if TYPE_CHECKING:
    from unisense.application.services.recommendation_service import RecommendationService

logger = get_logger(__name__)

# Cevap önbelleği — aynı sorgu (+ history + model) için Gemini'yi tekrar çağırmaktan kaçın.
# maxsize=512 ~5 MB civarı; ttl=3600 (1 saat) — guncel veri sınırı.
_response_cache: TTLCache[str, str] = TTLCache(maxsize=512, ttl=3600)


def _make_cache_key(query: Query, model_pref: str, user_context: dict | None = None) -> str:
    """Sorgu + top_k + history + model (+ profil puanları) → deterministic anahtar.

    user_context KPSS/DGS cevabını kişiselleştirir — anahtara girmezse bir
    kullanıcının puanına göre üretilen cevap başkasına servis edilir.
    """
    parts = [query.text.strip(), model_pref, str(getattr(query, "top_k", ""))]
    if user_context:
        parts.append(str(sorted(user_context.items())))
    if query.history:
        for t in query.history[-8:]:  # son 8 mesaj
            parts.append(f"{t.role}:{t.text.strip()}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


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
    (re.compile(r"\bege\b"),                                              "sea_ege"),  # ege kısa, \b sonda kalsın
    (re.compile(r"\bakdeniz"),                                            "sea_akdeniz"),
    (re.compile(r"\bbo(ğ|g)az\s*manzara"),                                "sea_marmara"),
]

# Şehir adından sonra gelebilecek ekler (fold'lu). Serbest önek eşleşmesi
# TUZAK: "bölüm"→"bolum" BOLU'yu, "karşı"→"karsi" KARS'ı yakalıyordu.
_CITY_SUFFIX = (r"(?:'?(?:da|de|ta|te|dan|den|tan|ten|daki|deki|taki|teki"
                r"|ya|ye|yi|yu|nin|nun|un|in|la|le|sinda|sinde))?\b")


# 81 il — sorgudan şehir tespiti için (geo.REGIONS'tan düzleştirilmiş)
def _city_patterns() -> list[tuple["re.Pattern[str]", str]]:
    from unisense.core.text import fold_tr
    from unisense.domain.geo import REGIONS

    pats = []
    for cities in REGIONS.values():
        for city in cities:
            # fold'lu anahtar: "sanliurfa" da "şanlıurfa" da yakalanır;
            # sadece bilinen ekler kabul — "bolum" BOLU değildir
            low = fold_tr(city)
            pats.append((re.compile(rf"\b{re.escape(low)}{_CITY_SUFFIX}"), city))
    return pats


_CITY_PATTERNS: list[tuple["re.Pattern[str]", str]] | None = None


# "X bölümü NEREDE/HANGİ üniversitede var?" kalıpları — bölüm tespit
# edildiyse şehir/üni olmasa da envanter listesi gerektirir (RAG'e gitmesin;
# vektör arama bu soruları üniversite-wiki mahallesine savurabiliyor)
_WHERE_PATTERNS = [
    re.compile(r"hangi\s+(ü|u)niversite"),
    re.compile(r"\bnerede\b|\bnerelerde\b|\bhangi\s+(ş|s)ehir"),
    re.compile(r"\bnereler(i|e)?\b"),  # "nereleri tercih etmeliyim / nerelere girerim"
    re.compile(r"\bvar\s*m(ı|i)\b"),
    re.compile(r"\bbulunan\b|\bbulunuyor\b|\ba(ç|c)an\b"),
    re.compile(r"\blistele\b|\bt(ü|u)m(ü|u)n(ü|u)\b"),
]

# Sayım/envanter soruları — "toplam kaç tane X programı var (elinde)?"
# RAG top_k=12 ile sayım yapılamaz; yapısal veriden gerçek toplam gerekir
_COUNT_RE = re.compile(
    r"ka(ç|c)\s*(tane|adet|program|b(ö|o)l(ü|u)m|(ü|u)niversite|kod)|"
    r"toplam\s+ka(ç|c)|say(ı|i)s(ı|i)\s+(ka(ç|c)|nedir|ne)", re.I)

# "24 tane tercih yap" / "tercih listesi oluştur" — N tercihlik liste isteği
_TERCIH_N_RE = re.compile(r"(\d{1,2})\s*(?:tane|adet)?\s*tercih", re.I)
_TERCIH_LIST_RE = re.compile(
    r"tercih\s*(listesi|yap|olu(ş|s)tur|haz(ı|i)rla|ver|et)", re.I)

# "kaç net yapmalıyım" — bölümün tabanına ulaşmak için tahmini net.
# 'internet' vb. eşleşmesin diye net'te \b sınırı.
_NET_RE = re.compile(
    r"\bka(ç|c)\s*net\b|\bnet\s*(yap|gerek|laz(ı|i)m|olmal|yeter|at(ı|i)|istiyor)",
    re.I)

# Takip (refinement) mesajı işaretleri — "tüm illerde bak", "peki", "diğerleri"...
# Tek başına konu içermeyen bu mesajlar önceki soruyla birleştirilir (bağlam).
_FOLLOWUP_RE = re.compile(
    r"\b(t(ü|u)m(ü|u)?|hepsi(ni)?|b(ü|u)t(ü|u)n|di(ğ|g)er(ler(i|ini)?)?|ba(ş|s)ka|"
    r"peki|bunlar(dan|ı)?|hangi(leri|si)?|ayn(ı|i)|(ş|s)ehir|il(ç|c)e|iller|"
    r"o zaman|bi(r)?\s*de|de\s*bak|da\s*bak|nas(ı|i)l)\b", re.I)

# Kullanıcı KENDİ puanını kastediyor mu — "puanıma göre", "kazanabilir miyim",
# "girer/yeter/tutar mıyım". Profildeki YKS puanını devreye almak için.
_SELF_SCORE_RE = re.compile(
    r"puan(ı|i)m|s(ı|i)ra(la)?m|kazan(abil|(ı|i)r\s*m)|gir(er|ebilir)\s*m|"
    r"yeter\s*m|tutar\s*m|yazabil|(ş|s)ans(ı|i)m|nereye\s*gir|benim\s*puan", re.I)

# OBP / diploma notu — net tahminini kişiselleştirmek için (yoksa varsayılan ~50).
#   "obp 450" / "obp'm 420"   → OBP doğrudan (0-500), katkı = OBP×0.12
#   "diploma notum 90" / "ortalamam 85" → not (0-100), OBP = not×5, katkı = not×0.6
# "obp 450", "obp'm 420", "obpm: 400" — ek/tırnak/işaret araya girebilir
_OBP_RE = re.compile(r"\bobp[^\d]{0,6}(\d{2,3}(?:[.,]\d+)?)", re.I)
_DIPLOMA_RE = re.compile(
    r"(?:diploma|ortalama|not\s*ortalam\w*)[^\d]{0,12}(\d{1,3}(?:[.,]\d+)?)", re.I)


@lru_cache(maxsize=1)
def _group_token_index() -> dict[str, list[str]]:
    """Bölüm grubu adlarının ayırt edici token index'i (fold'lu).

    'gastronomi' → ['Gastronomi ve Mutfak Sanatları'] gibi. Çok yaygın
    token'lar ('muhendisligi' ~80 grupta) index'e alınmaz — yanlış tetikler.
    """
    from unisense.application.services.compass_taxonomy import get_taxonomy
    from unisense.core.text import fold_tr

    tok_to_groups: dict[str, set[str]] = {}
    for g in get_taxonomy()["departments"]:
        for t in re.findall(r"[a-zçğıöşü]+", fold_tr(g["name"])):
            # Jenerik kelimeler sorgularda bölüm kastı olmadan geçer — index dışı
            # ("bilgi" → "Koç üniversitesi hakkında BİLGİ ver" tuzağı)
            if len(t) >= 4 and t not in {
                "bilim", "bilimleri", "yonetimi", "sanatlari", "bilgi",
                "genel", "temel", "uygulamali", "hizmetleri", "sistemleri",
                "teknolojisi", "teknolojileri", "tasarimi",
            }:
                tok_to_groups.setdefault(t, set()).add(g["name"])
    # ≤8 gruba işaret eden token'lar ayırt edici sayılır
    return {t: sorted(gs) for t, gs in tok_to_groups.items() if len(gs) <= 8}


# Yaygın bölüm anahtar kelimeleri (kısmi eşleşme için)
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
                 cities, universities, geo_flags}
    Tetikleyiciler: sıra/puan VEYA coğrafi filtre VEYA (bölüm + şehir/üni)
    — "İstanbul'daki tıp fakülteleri kaç puan?" tarzı envanter soruları
    RAG'in top_k limitine takılır, yapısal listeleme gerekir.
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
                # Geçerli aralık: 100-600
                if not (100 <= score <= 600):
                    score = None
                break
            except (ValueError, IndexError):
                pass

    # Coğrafi flagler — sıra/puan olmadan da bunlar yakalanabilir
    geo_flags: list[str] = []
    for pat, label in _GEO_PATTERNS:
        if pat.search(q):
            geo_flags.append(label)

    # Şehir + bölüm eşleşmeleri fold'lu yapılır — kullanıcı "istanbul tip"
    # yazsa da (ASCII) "İstanbul tıp" yazsa da yakalanır
    from unisense.core.text import fold_tr

    qf = fold_tr(query)

    # Şehirler (81 il, ek almış halleriyle)
    global _CITY_PATTERNS
    if _CITY_PATTERNS is None:
        _CITY_PATTERNS = _city_patterns()
    cities: list[str] = []
    for pat, city in _CITY_PATTERNS:
        if pat.search(qf):
            cities.append(city)

    # Bölüm anahtar kelimeleri (fold'lu kıyas, orijinal kw döner).
    # Kelime BAŞI sınırı şart: "diş" mühen-DİS-liği içinde eşleşmesin
    # (soneki serbest bırak — "bilgisayar mühendis" → "mühendisliği" kasıtlı prefix)
    departments: list[str] = []
    for kw in _DEPT_KEYWORDS:
        if re.search(rf"(?<![a-z]){re.escape(fold_tr(kw))}", qf):
            departments.append(kw)

    # Taksonomi-tabanlı bölüm tespiti: sorgudaki ayırt edici kelimeler
    # ("gastronomi", "odyoloji"...) 604 grup adına karşı denenir — sabit
    # keyword listesinin kapsamadığı tüm bölümleri yakalar
    token_index = _group_token_index()
    q_words = set(re.findall(r"[a-zçğıöşü]+", qf))
    for w in q_words:
        if w in token_index and w not in [fold_tr(k) for k in departments]:
            departments.append(w)

    # "Nerede / hangi üniversitede / var mı" kalıbı
    is_where_query = any(p.search(q) or p.search(qf) for p in _WHERE_PATTERNS)

    # Sayım sorusu ("toplam kaç tane ... var") — bölümle birlikte tetikler
    is_count = bool(_COUNT_RE.search(q))

    # "kaç net gerekir" — bölüm tabanından tahmini net (tersine hesap)
    is_net = bool(_NET_RE.search(q))
    # Kullanıcı OBP/diploma verdiyse net tahmini kişiselleşir (yoksa varsayılan)
    obp_katki = _parse_obp_katki(q) if is_net else None

    # "N tane tercih yap" / "tercih listesi oluştur" — N tercihlik liste isteği
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

    # Üniversite adları (Hacettepe, Boğaziçi... — veri destekli, cache'li)
    universities: list[str] = []
    try:
        from unisense.application.services.recommendation_service import detect_universities
        universities = detect_universities(query)
    except Exception:  # noqa: BLE001 — veri dosyası yoksa (test ortamı) sessiz geç
        pass

    # Bölüm tespit edildiyse sayım/tercih-listesi/nerede soruları da yapısal
    # veri gerektirir (RAG'in top_k limiti sayamaz/24'lük liste kuramaz)
    has_listing_target = departments and (
        cities or universities or is_where_query or is_count or is_tercih_list
        or is_net)
    if rank is None and score is None and not geo_flags and not has_listing_target:
        return None

    # Puan türü
    score_type = "SAY"  # default
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


def _is_refinement(text: str) -> bool:
    """Kısa + takip-işareti taşıyan (kendi konusunu kurmayan) mesaj mı."""
    return len(re.findall(r"\w+", text)) <= 6 and bool(_FOLLOWUP_RE.search(text))


def _routing_text(query) -> str:
    """Yapısal yönlendirme için bağlamsal metin: kısa TAKİP mesajlarında önceki
    kullanıcı mesajlarını da kat (chat bağlam sürekliliği, çok-turlu).

    Örn: "kpss bilgisayar mühendisi" → "tüm illerde bak" → "peki en çoğu hangi il".
    Her takip mesajı tek başına konu içermez; RAG'e düşüp sapardı. Artık geriye
    doğru KONUYU KURAN mesaja kadar yürünüp birleştirilir (arada birkaç takip
    mesajı olsa da). Konu değişmişse (yeni bağımsız soru) DURULUR — eski konu
    taşınmaz. Sadece YÖNLENDİRME için; cevap/cache/LLM gerçek mesajı kullanır.
    """
    cur = query.text
    hist = getattr(query, "history", None) or []
    if not _is_refinement(cur):
        return cur  # kendi konusu var → birleştirme
    users = [t.text for t in hist if getattr(t, "role", None) == "user" and t.text]
    if not users:
        return cur
    # Geriye yürü: takip mesajlarını topla, ilk KONU-KURAN mesajda dur (onu da al)
    collected: list[str] = []
    for txt in reversed(users[-6:]):  # en fazla son 6 kullanıcı mesajı
        collected.append(txt)
        if not _is_refinement(txt):  # konuyu kuran mesaj → dur
            break
    collected.reverse()
    return "\n".join([*collected, cur])


@lru_cache(maxsize=1)
def _rankings_year() -> int:
    """Rankings verisinin yılı — LLM'e giden 'X verisi' etiketleri veriden
    türesin, yıllık senkronda elle güncelleme gerekmesin."""
    try:
        from unisense.application.services.recommendation_service import _load_data

        rankings, _, _ = _load_data()
        years = {r.get("year") for r in rankings[:500] if r.get("year")}
        return max(years) if years else 2025
    except Exception:  # noqa: BLE001
        return 2025


# === YKS net tahmini (TERSİNE: taban puanı → yaklaşık net) ===
# ÖSYM yerleştirme ≈ 100 + TYT_bloğu(max~160) + AYT_bloğu(max~240) + OBP×0.12.
# TUZAK: bir PUAN tek net kombinasyonuna karşılık gelmez (dağılım + OBP değişir);
# bu yüzden TAHMİNÎ. Basit-dürüst model: öğrenci TYT ve AYT'de AYNI oranda (f)
# doğru yapıyor + referans OBP varsayımı. Metinde "tahmini" olduğu belirtilir.
_OBP_KATKI = 50.0    # diploma ~85 → OBP ~420 → 420×0.12 ≈ 50 puan (VARSAYILAN)
_TYT_SORU = 120      # TYT toplam soru
_AYT_SORU = 80       # SAY/EA/SÖZ AYT toplam soru (~80)


def _parse_obp_katki(q: str) -> float | None:
    """Sorgudan OBP/diploma → yerleştirme puanına OBP katkısı (OBP×0.12).

    Kullanıcı verirse net tahmini kişiselleşir; yoksa None → varsayılan kullanılır.
    """
    m = _OBP_RE.search(q)
    if m:
        obp = float(m.group(1).replace(",", "."))
        if 0 <= obp <= 500:
            return round(obp * 0.12, 1)
    m = _DIPLOMA_RE.search(q)
    if m:
        nota = float(m.group(1).replace(",", "."))
        if 0 <= nota <= 100:  # 100'lük not → OBP = not×5 → katkı = not×5×0.12
            return round(nota * 5 * 0.12, 1)
    return None


def _estimate_nets(
    score: float | None, score_type: str, obp_katki: float | None = None
) -> dict | None:
    """Taban puanından yaklaşık net (TYT + AYT). Tahminî — bkz. üst not.

    obp_katki verilmezse varsayılan ~50 (diploma ~85) kullanılır.
    """
    if not score:
        return None
    katki = obp_katki if obp_katki is not None else _OBP_KATKI
    if score_type == "TYT":  # önlisans / TYT puanı → TYT-only puanı 100-500 ölçekli
        # (net katkısı ~400: katsayılar 3.3-3.4). ESKİ /160 lisans TYT-bloğu katkısıydı
        # → yüksek TYT tabanları için "120/120 net" gibi imkânsız değer çıkarıyordu.
        f = max(0.0, min(1.0, (score - 100 - katki) / 400))
        return {"tyt": round(f * _TYT_SORU), "ayt": None}
    f = max(0.0, min(1.0, (score - 100 - katki) / 400))  # TYT160 + AYT240
    return {"tyt": round(f * _TYT_SORU), "ayt": round(f * _AYT_SORU)}


def _build_listing_context(intent: dict, rec_service: "RecommendationService") -> str:
    """Sıra/puan VERİLMEDEN sorulan envanter soruları için program listesi.

    Örn: "İstanbul'daki tıp fakülteleri kaç puan, kontenjan kaç?"
    RAG top_k=12 ile ~98 programın tamamını getiremez; yapısal veriden
    eksiksiz liste + toplam kontenjan üretilir.
    """
    list_n = intent.get("list_n")
    result = rec_service.list_programs(
        cities=intent.get("cities") or None,
        uni_codes=intent.get("universities") or None,
        dept_keywords=intent.get("departments") or None,
        limit=max(30, (list_n or 0) + 6),  # N tercih istendiyse seçecek kadar ver
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
        # Burs bilgisi bölüm adında zaten varsa tekrarlama
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
        # Kullanıcının profil puanıyla ÖN-HESAPLANMIŞ değerlendirme (LLM atlamasın)
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


# === KPSS / DGS sorgu yönlendirmesi ===
# DİKKAT: tek başına "kadro" YKS bağlamında da geçer ("akademik kadro") —
# sadece kpss/memur/atanma kelimeleri yönlendirir
_KPSS_RE = re.compile(r"\bkpss\b|\bmemur(lug|luk|iyet|u|a)?\b|\batan(ma|abilir|(ı|i)r(ı|i)m)", re.I)
# Sınav adı geçmeyen genel yerleştirme soruları — kullanıcının profil
# yolu (exam_track) DGS/KPSS ise o kanala yönlendirilir
_GENERIC_PLACEMENT_RE = re.compile(
    r"nereye\s+(girebilir|yerle(ş|s))|hangi\s+(b(ö|o)l(ü|u)m|program|kadro)|"
    r"\byerle(ş|s)(ebilir|irim|me)\b|puan(ı|i)mla", re.I)
_DGS_RE = re.compile(
    r"\bdgs\b|dikey\s*ge(ç|c)i(ş|s)|"
    # önlisans mezununun "hangi lisansa geçerim" tipi soruları (BULGU #10)
    r"(ö|o)n\s*lisans.*(lisans|ge(ç|c))|lisansa\s+ge(ç|c)", re.I)
_KPSS_PUAN_RE = re.compile(r"\b(\d{2,3}(?:[.,]\d{1,3})?)\s*(?:kpss\s*)?puan")

# KPSS/DGS bölüm çıkarımında tier-3'te elenecek sorgu kelimeleri (fold'lu).
# kadro_ara/program_ara ham kelimeyi substring eşlediği için anlamlı meslek
# kelimesini seçip gerisini atmak yeterli.
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
    # İstatistik/toplam sorularının kelimeleri — bölüm SANILMAMALI (BULGU)
    "toplam", "kontenjan", "kisilik", "kisi", "kac", "adet", "acildi",
    "acilan", "acik", "kadar", "sayisi", "donem", "genel", "hepsi", "tum",
})

# Toplam/istatistik sorusu ("kaç kişilik açıldı", "toplam kontenjan/kadro")
_KPSS_AGG_RE = re.compile(
    r"topla(m|mda)|ka(ç|c)\s*(ki(ş|s)i|kadro|kontenjan|adet|memur)|"
    r"ka(ç|c)\s*ki(ş|s)ilik|kontenjan|ka(ç|c)\s*al(ı|i)m", re.I)


def _detect_city_in_query(qf: str) -> str | None:
    """Fold'lu sorgudan il tespiti (81 il, ekli haller). qf zaten fold_tr'li."""
    global _CITY_PATTERNS
    if _CITY_PATTERNS is None:
        _CITY_PATTERNS = _city_patterns()
    for pat, city in _CITY_PATTERNS:
        if pat.search(qf):
            return city
    return None


def _detect_bolum_in_query(query: str) -> str:
    """KPSS/DGS sorgusundan bölüm/meslek adı çıkar (BULGU #8/#13).

    kadro_ara/program_ara fold'lu substring + nitelik alan-kodu eşleştirdiği
    için ham bölüm ifadesi yeterli. Öncelik sırası:
      1) çok-kelimeli DEPT_KEYWORD ('bilgisayar mühendis', 'hemşirelik')
      2) taksonomi token'ı ('gastronomi', 'odyoloji')
      3) anlamlı tek kelime (stopword/şehir değil) → 'hemşire', 'tekniker', 'harita'
    """
    from unisense.core.text import fold_tr

    qf = fold_tr(query)
    # 1) en uzun DEPT_KEYWORD eşleşmesi (çok-kelimeli yüksek isabet)
    best = ""
    for kw in _DEPT_KEYWORDS:
        if fold_tr(kw) in qf and len(kw) > len(best):
            best = kw
    if best:
        return best
    # 2) taksonomi token'ı
    token_index = _group_token_index()
    words = re.findall(r"[a-zçğıöşü]+", qf)
    for w in words:
        if w in token_index:
            return w
    # 3) anlamlı tek kelime (şehir ve stopword'leri çıkar)
    city = _detect_city_in_query(qf)
    city_fold = fold_tr(city) if city else ""
    for w in words:
        if len(w) >= 4 and w not in _BOLUM_STOPWORDS and w != city_fold:
            return w
    return ""


def _estimate_kpss_net(puan: float | None) -> int | None:
    """KPSS puanından yaklaşık toplam GY+GK net (TERSİNE, tahminî).

    KPSS puanı ≈ 40 + 0.5×(GY+GK net) → net ≈ 2×(puan−40). GY+GK toplam 120 soru.
    Gerçek puan standart-sapma normalizasyonuyla hesaplanır → yaklaşık.
    """
    if not puan:
        return None
    return max(0, min(120, round(2 * (puan - 40))))


def _build_kpss_context(query: str, user_context: dict | None = None) -> str:
    """KPSS sorusu → aktif dönem kadroları + geçmiş tabanlarla context."""
    from unisense.core.di import get_kpss_service
    from unisense.core.text import fold_tr

    uc = user_context or {}
    qf = fold_tr(query)
    is_net = bool(_NET_RE.search(qf))  # "kaç net gerekir" — taban→net tahmini
    # Puan: önce sorgudan, yoksa profilden (KPSS aralığı 40-105)
    puan = uc.get("kpss_puan")
    m = _KPSS_PUAN_RE.search(qf)
    if m:
        v = float(m.group(1).replace(",", "."))
        if 40 <= v <= 105:
            puan = v
    # İstatistik/toplam sorusu mu ("kaç kişilik açıldı", "toplam kontenjan")
    is_agg = bool(_KPSS_AGG_RE.search(qf))
    # Bölüm + şehir: ortak tespit (BULGU #13/#14 — token index tek başına
    # "bilgisayar/hemşire" gibi meslekleri kaçırıyordu). Toplam sorusunda
    # bölüm ARAMA — "kaç kişilik" → "kişilik" bölüm sanılmasın (BULGU)
    bolum = "" if is_agg else _detect_bolum_in_query(query)
    il = _detect_city_in_query(qf)
    duzey = ("önlisans" if "onlisans" in qf or "on lisans" in qf
             else "ortaöğretim" if "ortaogretim" in qf or "lise" in qf
             else uc.get("kpss_duzey") or "lisans")

    r = get_kpss_service().kadro_ara(bolum=bolum, puan=puan, duzey=duzey, il=il, limit=15)
    # Dönem veriden okunur; tercih tarihi/"aktif" iddiası HARDCODE EDİLMEZ
    # (BULGU #15 — pencere kapanınca bayatlıyordu). Tarihi LLM'e söylemeyiz.
    donem = r.get("donem", "2026/1")
    # Dönem geneli özet HER ZAMAN başta — "kaç kişilik/toplam kontenjan" gibi
    # istatistik sorularını tekil örneklerle değil bütünle yanıtlar (BULGU)
    ozet = get_kpss_service().donem_ozeti()
    dz = ozet["duzeyler"]
    dz_str = ", ".join(
        f"{d} {v['kadro']} kadro/{v['kontenjan']} kişi"
        for d, v in dz.items())
    lines = [f"=== KPSS {donem} MERKEZİ YERLEŞTİRME (B GRUBU) KADROLARI ===",
             f"DÖNEM GENELİ: toplam {ozet['toplam_kadro']} kadro, "
             f"{ozet['toplam_kontenjan']} kişilik kontenjan "
             f"({ozet['kurum_sayisi']} kurum, {ozet['il_sayisi']} il). "
             f"Düzey kırılımı: {dz_str}.",
             f"Filtre: düzey={duzey}, bölüm={bolum or 'tümü'}, "
             f"il={il or 'tümü'}, puan={puan or '?'}",
             f"Bu filtreye uyan: {r['total']} kadro / "
             f"{r.get('toplam_kontenjan', 0)} kişilik (ilk 15 örnek)", ""]
    # Öğretmenlik niyeti (BULGU #21): aşağıdaki B grubu kadrolar öğretmenlik
    # DEĞİL — LLM'i baştan uyar ki 'matematik' filtresini yanlış yorumlamasın
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
    """DGS sorusu → puana uygun lisans programları context'i."""
    from unisense.core.di import get_dgs_service
    from unisense.core.text import fold_tr

    uc = user_context or {}
    qf = fold_tr(query)
    puan = uc.get("dgs_puan")
    # 'puan' bağlamı ZORUNLU — aksi halde kontenjan/soru sayısı/yıl gibi 3-haneli
    # sayı puan sanılıp profildeki gerçek dgs_puan'ı EZİYORDU.
    mp = re.search(r"\b(\d{3}(?:[.,]\d{1,3})?)\s*puan", qf)
    if mp:
        v = float(mp.group(1).replace(",", "."))
        if 140 <= v <= 500:
            puan = v
    pt = ("EA" if re.search(r"\bea\b|esit", qf)
          else "SÖZ" if re.search(r"\bsoz(el)?\b", qf)
          else "SAY" if re.search(r"\bsay(isal)?\b", qf)
          else uc.get("dgs_turu") or "SAY")
    # Bölüm + şehir: KPSS ile aynı ortak tespit (BULGU #8/#14)
    bolum = _detect_bolum_in_query(query)
    il = _detect_city_in_query(qf)

    r = get_dgs_service().program_ara(puan_turu=pt, puan=puan, bolum=bolum, il=il, limit=15)
    lines = [f"=== DGS LİSANS GEÇİŞ PROGRAMLARI ({r.get('yil', _rankings_year())} tabanları) ===",
             f"Filtre: puan türü={pt}, puan={puan or '?'}, "
             f"bölüm={bolum or 'tümü'}, il={il or 'tümü'}",
             f"Uyan program sayısı: {r['total']} (ilk 15)", ""]
    for it in r["items"]:
        taban = f"taban {it['min_puan']:.2f}" if it["min_puan"] else "geçen yıl boş"
        lines.append(f"• [{it['department_code']}] {it['program_adi']} ({it['city']}) "
                     f"— {taban}, kontenjan {it['kontenjan']}")
    lines.append("")
    lines.append(r["uyari"])
    return "\n".join(lines)


def _build_recommendation_context(intent: dict, rec_service: "RecommendationService") -> str:
    """Intent → recommendation servisi → kısa context string."""
    # Sıra/puan yoksa bu bir envanter sorusu — kişisel öneri yerine liste dön
    if intent.get("rank") is None and intent.get("score") is None:
        listing = _build_listing_context(intent, rec_service)
        if listing:
            return listing
        # Liste boş döndüyse (filtre tutmadı) normal akışa düş

    try:
        st_enum = ScoreType(intent["score_type"]) if isinstance(intent["score_type"], str) else intent["score_type"]
    except ValueError:
        st_enum = ScoreType.SAY

    profile = StudentProfile(
        score_type=st_enum,
        score=intent.get("score"),
        rank=intent.get("rank"),
        preferred_cities=intent.get("cities") or [],
        preferred_uni_types=intent.get("uni_types") or [],
        preferred_departments=intent.get("departments") or [],
    )
    # Geo flagleri profile attach et — RecommendationService bunları okuyacak
    geo_flags = intent.get("geo_flags") or []
    setattr(profile, "_geo_flags", geo_flags)
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

    # N tercih istendiyse kovaları N'e kadar genişlet (varsayılan 8/10/5 = 23,
    # "24 tercih yap" için yetmez)
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
    """Kullanıcının profil sınav verilerinden kompakt 'KENDİ verisi' bloğu.

    Her mesajda LLM'e verilir → 'puanım/sıralamam/kazanabilir miyim' sorularını
    doğrudan yanıtlar, 'kişisel veriye erişemem' DEMEZ. YKS sırası tek kaynaktan
    (profildeki kayıtlı sıra, yoksa puandan tahmin) → tutarlı.
    """
    if not uc:
        return ""
    rows: list[str] = []
    yks_p = uc.get("yks_puan")
    if yks_p:
        tur = uc.get("yks_turu") or "SAY"
        sira = uc.get("yks_sira")
        if not sira:  # profilde sıra yoksa puandan tahmin (tek tutarlı kaynak)
            try:
                from unisense.application.services.recommendation_service import (
                    tahmini_sira,
                )
                est = tahmini_sira(float(yks_p), tur)
                sira = est["tahmini_sira"] if est else None
            except Exception:  # noqa: BLE001
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
    if not rows:
        return ""
    return (
        "=== KULLANICI SINAV PROFİLİ (bu kişinin KENDİ kayıtlı verisi) ===\n"
        + "\n".join(f"- {r}" for r in rows)
        + "\nYÖNERGE: Bu, kullanıcının profilinden SANA verilen KENDİ verisidir. "
        "'puanım/sıralamam/kazanabilir miyim' gibi ifadelerde bunu DOĞRUDAN kullan. "
        "ASLA 'kişisel verine erişemem' deme — erişimin var, yukarıda listeli. Sıra "
        "sorulursa yukarıdaki TEK sırayı kullan (farklı sıra uydurma, tutarlı ol)."
    )


class AskService:
    """RAG (Gemini + ChromaDB) + sıra/puan intent → Recommend hybrid."""

    def __init__(
        self,
        retrieval: RetrievalService,
        llm: LLMProvider,
        recommendation: "RecommendationService | None" = None,
    ) -> None:
        self._retrieval = retrieval
        self._llm = llm
        self._recommendation = recommendation

    def execute(self, query: Query, user_context: dict | None = None) -> Answer:
        start = time.perf_counter()

        # 0. Cache check — aynı sorgu+history+model son 1 saat içinde cevaplanmış mı?
        model_pref = getattr(query, "model_preference", None) or "gemini"
        cache_key = _make_cache_key(query, model_pref, user_context)
        cached_text = _response_cache.get(cache_key)
        if cached_text is not None:
            # Cache'de cevap var — retrieval yine yap (frontend kaynak chunk'larını bekliyor),
            # ama LLM çağırma. Toplam latency ~50-300ms.
            docs = self._retrieval.retrieve(query)
            total_ms = int((time.perf_counter() - start) * 1000)
            logger.info("ask_cache_hit", cache_key=cache_key[:8], total_ms=total_ms)
            return Answer(
                query=query.text,
                text=cached_text,
                docs=docs,
                total_latency_ms=total_ms,
            )

        # 0b. KPSS / DGS sorguları — kendi yapısal veri kaynaklarına yönlenir
        # (YKS RAG'i bu soruları cevaplayamaz; kadro/geçiş verisi ayrı)
        # ROUTING metni bağlamsaldır: kısa takip mesajları ("tüm illerde bak")
        # önceki soruyla birleşir (bkz. _routing_text) → chat bağlamı korunur.
        rt = _routing_text(query)
        sinav_context = ""
        uc_track = (user_context or {}).get("exam_track")
        try:
            if _KPSS_RE.search(rt):
                sinav_context = _build_kpss_context(rt, user_context)
                logger.info("kpss_intent_routed")
            elif _DGS_RE.search(rt):
                sinav_context = _build_dgs_context(rt, user_context)
                logger.info("dgs_intent_routed")
            elif uc_track == "KPSS" and (
                _GENERIC_PLACEMENT_RE.search(rt)
                or _KPSS_AGG_RE.search(rt)
            ):
                # Sınav adı yazılmamış ama kullanıcının yolu KPSS —
                # "toplam kaç kontenjan" gibi istatistik soruları da dahil
                sinav_context = _build_kpss_context(rt, user_context)
                logger.info("kpss_intent_routed", via="exam_track")
            elif uc_track == "DGS" and _GENERIC_PLACEMENT_RE.search(rt):
                sinav_context = _build_dgs_context(rt, user_context)
                logger.info("dgs_intent_routed", via="exam_track")
        except Exception as e:  # noqa: BLE001
            logger.warning("sinav_context_failed", error=str(e)[:200])

        # 1. Intent kontrolü — sıra/puan tabanlı sorgu mu? (bağlamsal metinle)
        intent = _extract_intent(rt) if not sinav_context else None

        # 1b. PROFİL YKS PUANI — kullanıcı mesajda puan yazmadıysa profildekini kullan
        # ("puanıma göre X kazanabilir miyim"). Mesajdaki açık puan HER ZAMAN öncelikli.
        uc = user_context or {}
        yks_puan = uc.get("yks_puan")
        if yks_puan and not sinav_context:
            if intent is not None and intent.get("score") is None and intent.get("rank") is None:
                # Bölüm/üni sorusu var, puan yok → profildeki puanı KIYAS için kat
                intent["user_score"] = yks_puan
                intent["user_score_type"] = uc.get("yks_turu")
                intent["user_rank"] = uc.get("yks_sira")
            elif intent is None and _SELF_SCORE_RE.search(rt):
                # "puanıma göre nereye girerim" — mesajda bölüm de yok → profilden öneri
                intent = {
                    "rank": uc.get("yks_sira"), "score": yks_puan,
                    "score_type": uc.get("yks_turu") or "SAY",
                    "uni_types": [], "departments": [], "cities": [], "universities": [],
                    "geo_flags": [], "is_count": False, "is_net": False,
                    "obp_katki": None, "list_n": None,
                }

        rec_context = ""
        if intent and self._recommendation is not None:
            try:
                rec_context = _build_recommendation_context(intent, self._recommendation)
                logger.info(
                    "intent_routed",
                    rank=intent.get("rank"),
                    score=intent.get("score"),
                    score_type=intent.get("score_type"),
                    uni_types=intent.get("uni_types"),
                    departments=intent.get("departments"),
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("intent_build_failed", error=str(e)[:200])

        # 2. Retrieval (RAG chunks)
        docs = self._retrieval.retrieve(query)
        rag_context = self._retrieval.build_context(docs)

        # 2b. Trend tespiti — kullanıcı "yıllar içinde / trend / geçmiş" sorduysa
        # ve retrieval'da program chunk'ı varsa, çoklu yıl trend özeti ekle
        trend_context = ""
        q_lower = _tr_lower(query.text)
        is_trend_query = any(p.search(q_lower) for p in _TREND_PATTERNS)
        if is_trend_query:
            program_codes_in_docs = list({d.department_code for d in docs if d.department_code})[:5]
            trend_lines = []
            for code in program_codes_in_docs:
                summary = trend_summary(code)
                if summary:
                    trend_lines.append(f"[{code}] {summary}")
            if trend_lines:
                trend_context = "=== ÇOKLU YIL TREND ===\n" + "\n\n".join(trend_lines)
                logger.info("trend_context_added", programs=len(trend_lines))
            elif not has_history():
                # History dosyası yoksa kullanıcıya açık not
                trend_context = (
                    "=== TREND NOTU ===\n"
                    f"Şu anda {_rankings_year()} verisi var. Geçmiş yıl arşivi "
                    f"({_rankings_year() - 5}-{_rankings_year() - 1}) hazırlanıyor — "
                    "trend sorularına şu an cevap için Wikipedia/üni sayfalarındaki sözel "
                    "bilgilerle yetinin."
                )

        # 3. Context'i birleştir — PROFİL (en üstte), sınav, recommendation, trend, RAG
        parts = []
        profile_context = _build_profile_context(uc)
        if profile_context:
            parts.append(profile_context)
        if sinav_context:
            parts.append(sinav_context)
        if rec_context:
            parts.append(rec_context)
        if trend_context:
            parts.append(trend_context)
        if rag_context:
            parts.append("=== EK RAG KAYNAKLARI ===\n" + rag_context)
        context = "\n\n".join(parts) if parts else rag_context

        # 4. LLM cevabı (multi-turn destekli — history varsa)
        history_dicts = []
        if query.history:
            for t in query.history:
                history_dicts.append({"role": t.role, "text": t.text})

        text = ""
        llm_ok = False
        try:
            text = self._llm.generate(
                query.text,
                context=context,
                history=history_dicts if history_dicts else None,
            )
            llm_ok = True
        except Exception as e:  # noqa: BLE001
            # Ham exception (model adı/kota/kaynak yolu vb.) kullanıcı balonuna SIZMASIN
            logger.warning("llm_failed", error=str(e)[:200])
            text = "⚠️ Şu an cevap üretemedim, lütfen birazdan tekrar dene."

        # Cevabı önbelleğe yaz (sadece başarılı LLM cevabı için, hata mesajını cache'leme)
        if llm_ok and text:
            _response_cache[cache_key] = text

        total_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ask_completed",
            query_len=len(query.text),
            docs=len(docs),
            has_recommendation=bool(rec_context),
            total_ms=total_ms,
            cache_size=len(_response_cache),
        )

        return Answer(
            query=query.text,
            text=text,
            docs=docs,
            total_latency_ms=total_ms,
        )
