"""AI Koç sistem aksiyonları — doğal Türkçe komutları güvenli, şemalı aksiyonlara çevirir."""
from __future__ import annotations

import json
import math
import re

from unisense.domain.models.query import CoachAction

_VALID_SINAV = ("YKS", "KPSS", "DGS", "LGS")
_VALID_PROFILE_SINAV = ("YKS", "KPSS", "DGS", "LGS", "TUS", "DUS", "AGS")
_VALID_PREF_SINAV = ("YKS", "KPSS", "DGS", "TUS", "DUS", "LGS")
_VALID_ACTION_TYPES = frozenset({
    "set_daily_goal",
    "create_study_plan",
    "log_questions",
    "add_task",
    "mark_topic_done",
    "add_preference",
    "add_deneme",
    "complete_task",
    "add_note",
    "log_study_time",
    "update_profile",
    "remove_preference",
    "reorder_preferences",
    "delete_task",
    "reschedule_task",
    "complete_note",
    "delete_note",
    "unmark_topic_done",
    "open_compare",
})
_ACTIONS_TAG_RE = re.compile(r"<UNISENSE_ACTIONS>\s*(.*?)\s*</UNISENSE_ACTIONS>", re.DOTALL | re.IGNORECASE)
_TR_LOWER_MAP = str.maketrans({"İ": "i", "I": "ı"})
_TR_UPPER_MAP = {"i": "İ", "ı": "I"}

_NOISE_WORDS = (
    "bugün", "bugun", "dün", "dun", "yarın", "yarin", "lütfen", "lutfen",
    "bana", "sistemde", "sisteme", "şimdi", "simdi", "ben", "bir",
)

# Geçerli deneme ders anahtarları ve soru üst sınırları (yksHesap.ts ile senkron)
_DENEME_FIELD_LIMITS: dict[str, int] = {
    "kpss_gy": 60, "kpss_gk": 60,
    "dgs_say": 50, "dgs_soz": 50,
    "lgs_tr": 20, "lgs_mat": 20, "lgs_fen": 20, "lgs_ink": 10, "lgs_din": 10, "lgs_ing": 10,
    "tyt_tr": 40, "tyt_sos": 20, "tyt_mat": 40, "tyt_fen": 20,
    "ayt_mat": 40, "ayt_fiz": 14, "ayt_kim": 13, "ayt_biy": 13,
    "ayt_edb": 24, "ayt_tar1": 10, "ayt_cog1": 6,
    "ayt_tar2": 11, "ayt_cog2": 11, "ayt_fel": 12, "ayt_din": 6,
    "ayt_dil": 80,
}

_DENEME_FIELD_ALIASES: dict[str, str] = {
    "gy": "kpss_gy",
    "gk": "kpss_gk",
    "tyt_tur": "tyt_tr",
    "tyt_turkce": "tyt_tr",
    "ayt_edebiyat": "ayt_edb",
    "lgs_tur": "lgs_tr",
    "lgs_turkce": "lgs_tr",
}

_DENEME_FIELD_LABELS: dict[str, str] = {
    "kpss_gy": "Genel Yetenek",
    "kpss_gk": "Genel Kültür",
    "dgs_say": "DGS Sayısal",
    "dgs_soz": "DGS Sözel",
    "lgs_tr": "LGS Türkçe",
    "lgs_mat": "LGS Matematik",
    "lgs_fen": "LGS Fen",
    "lgs_ink": "LGS İnkılap",
    "lgs_din": "LGS Din",
    "lgs_ing": "LGS İngilizce",
    "tyt_tr": "TYT Türkçe",
    "tyt_sos": "TYT Sosyal",
    "tyt_mat": "TYT Matematik",
    "tyt_fen": "TYT Fen",
    "ayt_mat": "AYT Matematik",
    "ayt_fiz": "AYT Fizik",
    "ayt_kim": "AYT Kimya",
    "ayt_biy": "AYT Biyoloji",
    "ayt_edb": "AYT Edebiyat",
    "ayt_tar1": "AYT Tarih-1",
    "ayt_cog1": "AYT Coğrafya-1",
    "ayt_tar2": "AYT Tarih-2",
    "ayt_cog2": "AYT Coğrafya-2",
    "ayt_fel": "AYT Felsefe",
    "ayt_din": "AYT Din",
    "ayt_dil": "YDT Dil",
}

# Doğru-yanlış eşleşme kalıpları (bitişik "50doğru 5yanlış" dahil)
_SCORE_PAIR_RE = re.compile(
    r"(\d{1,3})\s*(?:doğru|dogru|d)\b\s*(?:[,;/\-]|\bve\b|\s)*(\d{1,3})\s*(?:yanlış|yanlis|y)\b"
    r"|(\d{1,3})(?:doğru|dogru)\s*(?:[,;/\-]|\bve\b|\s)*(\d{1,3})(?:yanlış|yanlis)",
    re.IGNORECASE,
)
_SOLO_DOGRU_RE = re.compile(
    r"(\d{1,3})\s*(?:doğru|dogru)(?!\s*(?:[,;/\-]|\bve\b|\s)*\d{1,3}\s*(?:yanlış|yanlis|y))",
    re.IGNORECASE,
)


def _tr_lower(text: str) -> str:
    return text.translate(_TR_LOWER_MAP).lower()


def _tr_title(text: str) -> str:
    words = [w for w in text.strip().split() if w]
    out: list[str] = []
    for w in words:
        if len(w) >= 2 and w.isupper():
            out.append(w)
            continue
        first = _TR_UPPER_MAP.get(w[0], w[0].upper())
        out.append(first + w[1:])
    return " ".join(out)


def _round_half_up(value: float) -> float:
    return math.floor(value * 100.0 + 0.5) / 100.0


def _detect_any_sinav(q_lower: str, user_context: dict | None = None, allowed: tuple[str, ...] = _VALID_SINAV) -> str:
    if re.search(r"\bkpss\b|genel\s+yetenek|genel\s+k(?:ü|u)lt(?:ü|u)r", q_lower) and "KPSS" in allowed:
        return "KPSS"
    if re.search(r"\bdgs\b", q_lower) and "DGS" in allowed:
        return "DGS"
    if re.search(r"\blgs\b|ink(?:ı|i)lap|lise\b", q_lower) and "LGS" in allowed:
        return "LGS"
    if re.search(r"\btus\b", q_lower) and "TUS" in allowed:
        return "TUS"
    if re.search(r"\bdus\b", q_lower) and "DUS" in allowed:
        return "DUS"
    if re.search(r"\bags\b", q_lower) and "AGS" in allowed:
        return "AGS"
    if re.search(r"\b(?:yks|tyt|ayt|ydt)\b", q_lower) and "YKS" in allowed:
        return "YKS"
    track = str((user_context or {}).get("exam_track") or "").upper()
    return track if track in allowed else "YKS"


def _detect_sinav(q_lower: str, user_context: dict | None = None) -> str:
    return _detect_any_sinav(q_lower, user_context, _VALID_SINAV)


def _strip_ablative(word: str) -> str:
    """Türkçe yönelme/ayrılma ekini nazikçe sadeleştir (paragraftan -> Paragraf)."""
    w = word.strip(" ,.:;!?\"'")
    w_low = _tr_lower(w)
    for suf in ("konusundan", "dersinden", "testinden", "konusu"):
        if w_low.endswith(suf) and len(w_low) > len(suf) + 2:
            w = w[:-len(suf)].strip()
            w_low = _tr_lower(w)
            break
    for suf in ("'tan", "'ten", "'dan", "'den", "tan", "ten", "dan", "den"):
        if w_low.endswith(suf) and len(w_low) > len(suf) + 3:
            w = w[:-len(suf)].strip("'")
            break
    w = w.strip(" ,.:;!?\"'")
    if not w:
        return ""
    return _TR_UPPER_MAP.get(w[0], w[0].upper()) + w[1:]


def _extract_subject_before_questions(raw: str, match_start: int) -> str:
    prefix = raw[:match_start].strip()
    if not prefix:
        return ""
    tokens = [t for t in re.split(r"\s+", prefix) if t]
    cleaned: list[str] = []
    for tok in tokens:
        t_low = _tr_lower(tok.strip(",.:;!?"))
        if t_low in _NOISE_WORDS or t_low in ("yks", "tyt", "ayt", "kpss", "dgs", "lgs", "günde", "gunde", "günlük", "gunluk", "her", "gün"):
            continue
        cleaned.append(tok)
    if not cleaned:
        return ""
    tail = " ".join(cleaned[-2:])
    return _strip_ablative(tail)


def detect_preference_add_intent(query_text: str) -> bool:
    """Kullanıcı açıkça bulunan programları tercih listesine eklemeyi istiyor mu?"""
    q_low = _tr_lower(query_text)
    return bool(
        re.search(
            r"(?:tercih(?:ler)?(?:im)?(?:e|ime)?|tercih\s+listem(?:e)?|listem(?:e)?)\b.{0,40}?\b(?:ekle|kaydet|al|koy)\b",
            q_low,
        )
    )


def has_user_action_intent(query_text: str) -> bool:
    """Dolaylı RAG prompt-injection engeli: kullanıcının kendi sorusunda aksiyon niyeti var mı?"""
    q_low = _tr_lower(query_text)
    if detect_preference_add_intent(query_text):
        return True
    return bool(
        re.search(
            r"(?:hedef|kota|soru|plan|program|bitir|tamamla|işaretle|isaretle|ekle|kaydet|koy|ayarla|olsun|"
            r"çözdüm|cozdum|yaptım|yaptim|güncelle|guncelle|deneme|doğru|dogru|yanlış|yanlis|not\b|dakika|\bdk\b|"
            r"saat|çalıştım|calistim|sıralama|siralama|sıram|siram|obp|puanım|puanim|yüzdelik|yuzdelik|"
            r"sil|çıkar|cikar|kaldır|kaldir|ertele|taşı|tasi|sırala|sirala|düzenle|duzenle|karşılaştır|karsilastir|geri\s+al)",
            q_low,
        )
    )


def is_pure_coach_command(query_text: str, actions: list[CoachAction]) -> bool:
    """Sorgu ÖSYM/YÖK Atlas veri araması değil yalnızca kişisel koç/kayıt komutu mu?"""
    if not actions:
        return False
    if detect_preference_add_intent(query_text):
        return False
    if any(a.type in ("open_compare", "remove_preference", "reorder_preferences") for a in actions):
        return False
    q_low = _tr_lower(query_text)
    return not re.search(
        r"\b(?:kadro\w*|atama\w*|taban\w*|tavan\w*|kontenjan\w*|kazan\w*|gelir\s+mi|yeter\s+mi|"
        r"tercih\s+(?:list|öner|oner|yap)|(?:üniversite|universite|bölüm|bolum)\s+(?:öner|oner|bul|hangisi)|"
        r"akademisyen\w*|profesör\w*|profesor\w*|hangi\s+(?:şehir|il|üniversite|bölüm))\b",
        q_low,
    )


def is_personal_coaching_query(query_text: str, actions: list[CoachAction]) -> bool:
    """Saf kayıt komutu VEYA kullanıcının kendi deneme/görev/not/çalışma koçluğu sorusu mu?"""
    if is_pure_coach_command(query_text, actions):
        return True
    if actions or detect_preference_add_intent(query_text):
        return False
    q_low = _tr_lower(query_text)
    if re.search(
        r"\b(?:taban\w*|tavan\w*|kontenjan\w*|kazan\w*|gelir\s+mi|yeter\s+mi|"
        r"üni\w*|üniversite\w*|kadro\w*|atama\w*|takvim\w*|ne\s+zaman|kaç\s+gün\s+kaldı|"
        r"iş\s+ilan\w*|staj\s+ilan\w*|akademisyen\w*|lise\w*|uzmanlık\w*|tus\b|dus\b)\b",
        q_low,
    ):
        return False
    return bool(
        re.search(
            r"(?:deneme\w*\s+nasıl|son\s+deneme\w*|netlerim\b|netim\s+nasıl|bekleyen\s+görev\w*|görevlerim\b|"
            r"planım\s+nasıl|takvimim\s+nasıl|notlarım\w*|bugün\s+ne\s+çalış\w*|hangi\s+konudan\s+daha\s+çok\s+soru|"
            r"çalışma\s+tavsiyesi|çalışma\s+durumum|ilerlemem\s+nasıl|eksik\s+konularım)",
            q_low,
        )
    )


def _deneme_subject_specs(exam_sinav: str) -> list[tuple[str, str]]:
    if exam_sinav == "KPSS":
        return [
            (r"\bgenel\s+yetenek\b|\bgy\b", "kpss_gy"),
            (r"\bgenel\s+k(?:ü|u)lt(?:ü|u)r\b|\bgk\b", "kpss_gk"),
        ]
    if exam_sinav == "DGS":
        return [
            (r"\bsay(?:ı|i)sal\b|\bdgs\s*say\b", "dgs_say"),
            (r"\bs(?:ö|o)zel\b|\bt(?:ü|u)rk(?:ç|c)e\b|\bdgs\s*s(?:ö|o)z\b", "dgs_soz"),
        ]
    if exam_sinav == "LGS":
        return [
            (r"\bt(?:ü|u)rk(?:ç|c)e\b", "lgs_tr"),
            (r"\bmatematik\b|\bmat\b", "lgs_mat"),
            (r"\bfen(?:\s+bilimleri)?\b", "lgs_fen"),
            (r"\bink(?:ı|i)lap(?:\s+tarihi)?\b|\btarih\b", "lgs_ink"),
            (r"\bdin(?:\s+k(?:ü|u)lt(?:ü|u)r(?:ü|u))?\b", "lgs_din"),
            (r"\bingilizce\b|\bing\b", "lgs_ing"),
        ]
    # YKS (TYT / AYT)
    return [
        (r"\btyt\s*t(?:ü|u)rk(?:ç|c)e\b|\bt(?:ü|u)rk(?:ç|c)e\b", "tyt_tr"),
        (r"\btyt\s*sosyal\b|\bsosyal\b", "tyt_sos"),
        (r"\bayt\s*matematik\b|\bayt\s*mat\b", "ayt_mat"),
        (r"\btyt\s*matematik\b|\btyt\s*mat\b|\bmatematik\b|\bmat\b", "tyt_mat"),
        (r"\btyt\s*fen\b|\bfen\b", "tyt_fen"),
        (r"\bfizik\b|\bfiz\b", "ayt_fiz"),
        (r"\bkimya\b|\bkim\b", "ayt_kim"),
        (r"\bbiyoloji\b|\bbiy\b", "ayt_biy"),
        (r"\bedebiyat\b|\bedb\b", "ayt_edb"),
        (r"\btarih\s*-?\s*1\b", "ayt_tar1"),
        (r"\bco(?:ğ|g)rafya\s*-?\s*1\b", "ayt_cog1"),
        (r"\btarih\s*-?\s*2\b", "ayt_tar2"),
        (r"\bco(?:ğ|g)rafya\s*-?\s*2\b", "ayt_cog2"),
        (r"\bfelsefe\b|\bfel\b", "ayt_fel"),
        (r"\bdin\b", "ayt_din"),
        (r"\bydt\b|\byabanc(?:ı|i)\s+dil\b|\bingilizce\b", "ayt_dil"),
    ]


def _preview_deneme_metrics(sinav: str, exam_type: str | None, girdi: dict[str, dict[str, int]]) -> tuple[float, float]:
    """yksHesap.ts ile senkron net ve yaklaşık puan önizlemesi hesapla."""
    pen = (1.0 / 3.0) if sinav == "LGS" else 0.25
    nets: dict[str, float] = {}
    toplam_net = 0.0
    for field_id, dy in girdi.items():
        net = float(dy.get("d", 0)) - pen * float(dy.get("y", 0))
        nets[field_id] = net
        toplam_net += net

    puan = 0.0
    if sinav == "KPSS":
        gy = nets.get("kpss_gy", 0.0)
        gk = nets.get("kpss_gk", 0.0)
        if gy > 0 or gk > 0:
            puan = 40.0 + 0.5 * (gy + gk)
    elif sinav == "DGS":
        say_w = nets.get("dgs_say", 0.0)
        soz_w = nets.get("dgs_soz", 0.0)
        if exam_type == "EA":
            w = say_w * 3.3 + soz_w * 3.3
        elif exam_type == "SÖZ":
            w = say_w * 2.6 + soz_w * 4.0
        else:
            w = say_w * 4.0 + soz_w * 2.6
        if w > 0:
            puan = 100.0 + w
    elif sinav == "LGS":
        w_map = {"lgs_tr": 4.0, "lgs_mat": 4.0, "lgs_fen": 4.0, "lgs_ink": 1.0, "lgs_din": 1.0, "lgs_ing": 1.0}
        w = sum(nets.get(k, 0.0) * c for k, c in w_map.items())
        if any(v != 0.0 for v in nets.values()):
            puan = max(100.0, 100.0 + (w / 270.0) * 400.0)
    else:
        tyt_only = sum(
            nets.get(k, 0.0) * c
            for k, c in (("tyt_tr", 3.3), ("tyt_sos", 3.4), ("tyt_mat", 3.3), ("tyt_fen", 3.4))
        )
        has_ayt = any(k.startswith("ayt_") and nets.get(k, 0.0) != 0.0 for k in nets)
        if not has_ayt and tyt_only > 0:
            puan = 100.0 + tyt_only

    return _round_half_up(toplam_net), _round_half_up(puan)


def _extract_deneme_action(raw: str, q_low: str, fallback_sinav: str) -> CoachAction | None:
    has_deneme_kw = bool(re.search(r"\bdeneme(?:m|mi|si|sini|ye|de)?\b", q_low))
    has_kpss_pair_kw = bool(re.search(r"genel\s+yetenek", q_low) and re.search(r"genel\s+k(?:ü|u)lt(?:ü|u)r", q_low))
    if not (has_deneme_kw or has_kpss_pair_kw):
        return None

    exam_sinav = _detect_sinav(q_low, {"exam_track": fallback_sinav})
    exam_type: str | None = None
    if exam_sinav == "YKS":
        if re.search(r"\bydt\b|\bdil\b", q_low):
            exam_type = "DİL"
        elif re.search(r"\bs(?:ö|o)zel\b|\bedebiyat\b", q_low):
            exam_type = "SÖZ"
        elif re.search(r"\bea\b|\be(?:ş|s)it\s+a(?:ğ|g)(?:ı|i)rl(?:ı|i)k\b", q_low):
            exam_type = "EA"
        elif re.search(r"\bayt\b|\bfizik\b|\bkimya\b|\bbiyoloji\b|\bsay(?:ı|i)sal\b", q_low):
            exam_type = "SAY"
        else:
            exam_type = "TYT"
    elif exam_sinav == "DGS":
        if re.search(r"\bs(?:ö|o)zel\b", q_low):
            exam_type = "SÖZ"
        elif re.search(r"\bea\b|\be(?:ş|s)it\s+a(?:ğ|g)(?:ı|i)rl(?:ı|i)k\b", q_low):
            exam_type = "EA"
        else:
            exam_type = "SAY"

    # Deneme adını ayıkla ve sayı taramasını temizle
    ad = ""
    working_low = q_low
    name_m = re.search(
        r"(?:\bismi\b|\bad(?:ı|i)\b|\badl(?:ı|i)\b|\byay(?:ı|i)n(?:ı|i)?\b|\bdeneme\s+ad(?:ı|i)\b)\s*[:=]?\s*"
        r"([a-zçğıöşüA-ZÇĞİÖŞÜ0-9\s\-]{2,55}?)"
        r"(?=$|\s+(?:bug(?:ü|u)n|d(?:ü|u)n|olduk|çözdüm|cozdum|yapt(?:ı|i)m|ekle|kaydet|genel|t(?:ü|u)rk(?:ç|c)e|matematik|sosyal|fen|say(?:ı|i)sal|s(?:ö|o)zel)|\s+\d|[,.;])",
        raw,
        re.IGNORECASE,
    )
    if name_m:
        ad_raw = raw[name_m.start(1):name_m.end(1)].strip(" ,.:;!?\"'")
        ad = _tr_title(ad_raw)[:60]
        working_low = q_low[:name_m.start()] + " " + q_low[name_m.end():]
    else:
        quoted_m = re.search(r"[\"']([^\"']{2,55})[\"']\s*deneme", raw, re.IGNORECASE)
        if quoted_m:
            ad = _tr_title(quoted_m.group(1))[:60]

    # Doğru/yanlış çiftlerini bul
    pairs: list[tuple[int, int, int, int]] = []  # (start, end, d, y)
    for m in _SCORE_PAIR_RE.finditer(working_low):
        d = int(m.group(1) or m.group(3))
        y = int(m.group(2) or m.group(4))
        pairs.append((m.start(), m.end(), d, y))
    for m in _SOLO_DOGRU_RE.finditer(working_low):
        ms, me = m.start(), m.end()
        if any(not (me <= ps or ms >= pe) for ps, pe, _, _ in pairs):
            continue
        pairs.append((ms, me, int(m.group(1)), 0))
    pairs.sort(key=lambda item: item[0])
    if not pairs:
        return None

    # Ders eşleşmelerini bul (çakışan daha kısa eşleşmeleri ele)
    subj_hits: list[tuple[int, int, str]] = []
    for pat, fid in _deneme_subject_specs(exam_sinav):
        for m in re.finditer(pat, working_low):
            ms, me = m.start(), m.end()
            if any(not (me <= hs or ms >= he) for hs, he, _ in subj_hits):
                continue
            subj_hits.append((ms, me, fid))
    subj_hits.sort(key=lambda item: item[0])
    if not subj_hits:
        return None

    used_pair_idx: set[int] = set()
    used_subj_idx: set[int] = set()
    bound: dict[str, tuple[int, int]] = {}

    def _has_subj_between(a: int, b: int, skip_idx: int) -> bool:
        lo, hi = min(a, b), max(a, b)
        return any(idx != skip_idx and lo <= hs and he <= hi for idx, (hs, he, _) in enumerate(subj_hits))

    def _has_pair_between(a: int, b: int, skip_p: int) -> bool:
        lo, hi = min(a, b), max(a, b)
        return any(pi != skip_p and lo <= ps and pe <= hi for pi, (ps, pe, _, _) in enumerate(pairs))

    # Aşama 1: Açık bağlaçlı ileri eşleşme ("genel kültür ise 40 doğru 10yanlış", "matematik: 30d 5y")
    for si, (hs, he, fid) in enumerate(subj_hits):
        for pi, (ps, pe, d, y) in enumerate(pairs):
            if pi in used_pair_idx or ps < he:
                continue
            if _has_subj_between(he, ps, si) or _has_pair_between(he, ps, pi):
                continue
            between = working_low[he:ps].strip()
            if re.fullmatch(r"(?:ise|:|=|-)?", between):
                bound[fid] = (d, y)
                used_pair_idx.add(pi)
                used_subj_idx.add(si)
                break

    # Aşama 2: Kalan ders/çiftler için baskın sıra yönüne göre eşleştirme
    rem_subjs = [(si, hs, he, fid) for si, (hs, he, fid) in enumerate(subj_hits) if si not in used_subj_idx]
    rem_pairs = [(pi, ps, pe, d, y) for pi, (ps, pe, d, y) in enumerate(pairs) if pi not in used_pair_idx]

    if rem_subjs and rem_pairs:
        backward_dominant = rem_pairs[0][1] < rem_subjs[0][1] and rem_pairs[-1][2] <= rem_subjs[-1][1]
        if backward_dominant:
            # "<sayılar> <ders>" düzeni
            for si, hs, he, fid in rem_subjs:
                candidates = [
                    (pi, ps, pe, d, y)
                    for pi, ps, pe, d, y in rem_pairs
                    if pi not in used_pair_idx and pe <= hs
                    and not _has_subj_between(pe, hs, si)
                    and not _has_pair_between(pe, hs, pi)
                ]
                if candidates:
                    pi, _, _, d, y = candidates[-1]
                    bound[fid] = (d, y)
                    used_pair_idx.add(pi)
                    used_subj_idx.add(si)
        else:
            # "<ders> <sayılar>" veya karma düzen (önce ileri, yoksa geri)
            for si, hs, he, fid in rem_subjs:
                fwd = [
                    (pi, ps, pe, d, y)
                    for pi, ps, pe, d, y in rem_pairs
                    if pi not in used_pair_idx and ps >= he
                    and not _has_subj_between(he, ps, si)
                    and not _has_pair_between(he, ps, pi)
                ]
                if fwd:
                    pi, _, _, d, y = fwd[0]
                    bound[fid] = (d, y)
                    used_pair_idx.add(pi)
                    used_subj_idx.add(si)
                    continue
                bwd = [
                    (pi, ps, pe, d, y)
                    for pi, ps, pe, d, y in rem_pairs
                    if pi not in used_pair_idx and pe <= hs
                    and not _has_subj_between(pe, hs, si)
                    and not _has_pair_between(pe, hs, pi)
                ]
                if bwd:
                    pi, _, _, d, y = bwd[-1]
                    bound[fid] = (d, y)
                    used_pair_idx.add(pi)
                    used_subj_idx.add(si)

    if not bound:
        return None

    # Sınır doğrulaması (soru sayısı aşımı olmasın)
    girdi: dict[str, dict[str, int]] = {}
    for fid, (d, y) in bound.items():
        lim = _DENEME_FIELD_LIMITS.get(fid, 60)
        d_clamped = max(0, min(lim, d))
        y_clamped = max(0, min(lim - d_clamped, y))
        girdi[fid] = {"d": d_clamped, "y": y_clamped}

    toplam_net, puan = _preview_deneme_metrics(exam_sinav, exam_type, girdi)
    gun_offset = -1 if re.search(r"\b(?:dün|dun)\b", q_low) else 0
    ad_final = ad or f"{exam_sinav} Deneme"
    puan_str = f" · ~{puan:g} puan" if puan > 0 else ""

    payload: dict = {
        "sinav": exam_sinav,
        "ad": ad_final,
        "gun_offset": gun_offset,
        "girdi": girdi,
        "toplam_net_preview": toplam_net,
        "puan_preview": puan,
    }
    if exam_type and exam_sinav in ("YKS", "DGS"):
        payload["type"] = exam_type

    return CoachAction(
        type="add_deneme",
        label=f"{exam_sinav} · {ad_final}: {toplam_net:g} net{puan_str} kaydedildi",
        auto_apply=True,
        payload=payload,
    )


def extract_coach_actions(query_text: str, user_context: dict | None = None) -> list[CoachAction]:
    """Kullanıcı sorgusundan güvenli, şema doğrulamalı sistem aksiyonları çıkar."""
    raw = (query_text or "").strip()
    if not raw:
        return []
    q_low = _tr_lower(raw)
    sinav = _detect_sinav(q_low, user_context)
    actions: list[CoachAction] = []

    # 0) Deneme sonucu kaydı (KPSS/YKS/DGS/LGS) — eşleşirse ayrıca log_questions üretme
    deneme_action = _extract_deneme_action(raw, q_low, sinav)
    if deneme_action is not None:
        actions.append(deneme_action)
        sinav = deneme_action.payload["sinav"]

    # 1) Çözülen soru kaydı ("bugün paragraftan 40 soru çözdüm 35 doğru" veya "Matematikten 30 çözdüm 26 doğru")
    q_match = (
        re.search(r"(\d{1,4})\s*(?:tane\s*)?(?:soru|test\s*sorusu)", q_low)
        or re.search(r"(\d{1,4})\s+(?:çözdüm|cozdum|yaptım|yaptim)", q_low)
    )
    has_log_verb = bool(
        re.search(
            r"(?:çözdüm|cozdum|çözüldü|cozuldu|doğru|dogru|yanlış|yanlis|yaptım|yaptim|işledim|isledim|(?:bugün|bugun).*(?:kaydet|ekle))",
            q_low,
        )
    )
    is_goal_only = bool(re.search(r"hedef|günlük\s+\d+\s+soru\s+(?:koy|ayarla|olsun|yap|belirle)", q_low))
    if deneme_action is None and q_match and has_log_verb and not is_goal_only:
        cozulen = max(1, min(500, int(q_match.group(1))))
        dogru_m = re.search(r"(\d{1,4})\s*doğru|\b(\d{1,4})\s*d\b", q_low)
        yanlis_m = re.search(r"(\d{1,4})\s*yanlış|\b(\d{1,4})\s*y\b", q_low)
        if dogru_m:
            raw_d = int(dogru_m.group(1) or dogru_m.group(2))
            dogru = max(0, min(cozulen, raw_d))
        elif yanlis_m:
            raw_y = int(yanlis_m.group(1) or yanlis_m.group(2))
            dogru = max(0, cozulen - min(cozulen, raw_y))
        else:
            dogru = cozulen
        subj = _extract_subject_before_questions(raw, q_match.start())
        konu = subj or "Günlük Çalışma"
        ders = subj or "Genel"
        actions.append(
            CoachAction(
                type="log_questions",
                label=f"{sinav} · {konu}: {cozulen} soru ({dogru} doğru) kaydedildi",
                auto_apply=True,
                payload={
                    "sinav": sinav,
                    "ders": ders[:60],
                    "konu": konu[:120],
                    "cozulen": cozulen,
                    "dogru": dogru,
                },
            )
        )

    # 2) Çok-günlü veya haftalık çalışma planı ("30 günde konuları bitir, günde 40 soru")
    plan_days_m = re.search(
        r"(\d{1,3})\s*gün(?:de|lük|luk)\b.*?(?:plan|program|bitir|çalış|calis|hazırla|hazirla|kur|oluştur|olustur|dağıt|dagit)",
        q_low,
    )
    weekly_plan = bool(
        re.search(r"(?:haftalık|haftalik|bu\s+hafta)\s*(?:çalışma\s*)?(?:plan|program)\w*\s*(?:kur|oluştur|olustur|yap|hazırla)", q_low)
    )
    daily_q_m = re.search(
        r"(?:günlük|gunluk|günde|gunde|her\s*gün|her\s*gun)\s*(\d{1,4})\s*soru",
        q_low,
    ) or re.search(
        r"soru\s*(?:hedef\w*|kotası|kotasi|kota)\s*(?:[:=]|günlük|gunluk)?\s*(\d{1,4})",
        q_low,
    )
    gunluk_soru = max(5, min(1000, int(daily_q_m.group(1)))) if daily_q_m else None

    if plan_days_m or weekly_plan:
        gun_sayisi = int(plan_days_m.group(1)) if plan_days_m else 7
        gun_sayisi = max(1, min(365, gun_sayisi))
        soru_suffix = f", günde {gunluk_soru} soru" if gunluk_soru else ""
        actions.append(
            CoachAction(
                type="create_study_plan",
                label=f"{sinav} · {gun_sayisi} günlük çalışma planı oluşturuldu{soru_suffix}",
                auto_apply=True,
                payload={
                    "sinav": sinav,
                    "gun_sayisi": gun_sayisi,
                    "gunluk_soru": gunluk_soru,
                },
            )
        )
    elif deneme_action is None:
        # 3) Günlük soru / çalışma hedefi ("Bana günlük 40 soru hedefi koy")
        hour_m = re.search(r"(?:günde|gunde|günlük|gunluk)\s*(\d{1,2})\s*saat", q_low)
        week_hour_m = re.search(r"(?:haftada|haftalık|haftalik)\s*(\d{1,3})\s*saat", q_low)
        hedef_saat = None
        if week_hour_m:
            hedef_saat = max(1, min(100, int(week_hour_m.group(1))))
        elif hour_m:
            hedef_saat = max(1, min(100, int(hour_m.group(1)) * 7))

        hedef_bolum_m = re.search(
            r"(?:hedefim|hedef\s+bölüm(?:üm)?|hedef\s+üniversite(?:m)?)\s*[:=]?\s*([a-zçğıöşüA-ZÇĞİÖŞÜ\s\-]{3,60}?)(?=$|[,.;]|\s+(?:için|ve|günlük|günde))",
            raw,
        )
        hedef_bolum = None
        if hedef_bolum_m:
            cand = hedef_bolum_m.group(1).strip(" ,.:;!?")
            if _tr_lower(cand) not in ("koy", "yap", "ayarla", "belirle", "olsun", "ekle"):
                hedef_bolum = cand[:120]

        has_goal_cue = bool(
            re.search(r"hedef|koy|ayarla|olsun|güncelle|guncelle|belirle|planla|kota", q_low)
            or daily_q_m
        )
        if (gunluk_soru or hedef_saat or hedef_bolum) and has_goal_cue and not has_log_verb:
            parts_lbl = [sinav]
            if gunluk_soru:
                parts_lbl.append(f"günlük {gunluk_soru} soru hedefi")
            if hedef_saat:
                parts_lbl.append(f"haftalık {hedef_saat} saat")
            if hedef_bolum:
                parts_lbl.append(f"hedef {hedef_bolum}")
            actions.append(
                CoachAction(
                    type="set_daily_goal",
                    label=" · ".join(parts_lbl) + " kaydedildi",
                    auto_apply=True,
                    payload={
                        "sinav": sinav,
                        "gunluk_soru": gunluk_soru,
                        "hedef_saat": hedef_saat,
                        **({"hedef_bolum": hedef_bolum} if hedef_bolum else {}),
                    },
                )
            )

    # 4) Konu işareti kaldırma ("Türev konusunun işaretini kaldır / tamamlanmadı yap")
    unmark_m = re.search(
        r"([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,55}?)\s+konu(?:sunun|sunu|nu|yu|su)?\s*(?:işaretini\s*kaldır|isaretini\s*kaldir|geri\s*al|tamamlanmadı\s*yap|tamamlanmadi\s*yap|yapılmadı|yapilmadi)",
        q_low,
    )
    if unmark_m and not plan_days_m and deneme_action is None:
        konu_raw = raw[unmark_m.start(1):unmark_m.end(1)].strip(" ,.:;!?")
        konu_clean = " ".join(
            tok for tok in konu_raw.split()
            if _tr_lower(tok) not in ("bugün", "bugun", "yks", "tyt", "ayt", "kpss", "dgs", "lgs")
        )
        if konu_clean:
            actions.append(
                CoachAction(
                    type="unmark_topic_done",
                    label=f"{sinav} · '{konu_clean}' konusu tamamlanmadı işaretlendi",
                    auto_apply=True,
                    payload={"sinav": sinav, "konu": konu_clean[:120]},
                )
            )

    # 5) Konu tamamlandı işareti ("Türev konusunu bitirdim" / "Paragraf bitti")
    topic_m = None if unmark_m else (
        re.search(
            r"([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,55}?)\s+konu(?:sunu|nu|yu|su)?\s*(?:bitirdim|tamamladım|tamamladim|işaretle|isaretle|bitti)",
            q_low,
        ) or re.search(
            r"^([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,45}?)\s+(?:bitirdim|tamamladım|tamamladim|bitti\s*işaretle)$",
            q_low,
        )
    )
    if topic_m and not plan_days_m and deneme_action is None:
        konu_raw = raw[topic_m.start(1):topic_m.end(1)].strip(" ,.:;!?")
        konu_clean = " ".join(
            tok for tok in konu_raw.split()
            if _tr_lower(tok) not in ("bugün", "bugun", "yks", "tyt", "ayt", "kpss", "dgs", "lgs")
        )
        if konu_clean and not re.search(r"\d+\s*(?:soru|gün)", _tr_lower(konu_clean)):
            actions.append(
                CoachAction(
                    type="mark_topic_done",
                    label=f"{sinav} · '{konu_clean}' konusu tamamlandı işaretlendi",
                    auto_apply=True,
                    payload={"sinav": sinav, "konu": konu_clean[:120]},
                )
            )

    # 6) Görev silme / erteleme / tamamlama
    del_task_m = re.search(
        r"(?:bugünkü|bugunku|yarına|yarinki)?\s*([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,65}?)\s+görev(?:ini|i|imi)?\s*(?:sil|kaldır|kaldir|iptal(?:\s*et)?)",
        q_low,
    )
    resched_task_m = None if del_task_m else re.search(
        r"(?:bugünkü|bugunku|yarına|yarinki)?\s*([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,65}?)\s+görev(?:ini|i|imi)?\s*(yarına|yarina|bugüne|bugune)\s*(?:ertele|taşı|tasi|al|kaydır|kaydir)",
        q_low,
    )
    comp_m = None if (del_task_m or resched_task_m) else re.search(
        r"(?:bugünkü|bugunku|yarına|yarinki)?\s*([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,65}?)\s+görev(?:ini|i|imi)?\s*(?:tamamladım|tamamladim|bitirdim|yaptım|yaptim|işaretle|isaretle)",
        q_low,
    )
    if del_task_m and deneme_action is None:
        title_clean = " ".join(
            tok for tok in raw[del_task_m.start(1):del_task_m.end(1)].strip(" ,.:;!?").split()
            if _tr_lower(tok) not in ("bugünkü", "bugunku", "bugün", "bugun", "yks", "tyt", "ayt", "kpss", "dgs", "lgs")
        )
        if title_clean:
            actions.append(
                CoachAction(
                    type="delete_task",
                    label=f"{sinav} · '{title_clean[:80]}' görevi silindi",
                    auto_apply=True,
                    payload={"sinav": sinav, "title": title_clean[:120]},
                )
            )
    elif resched_task_m and deneme_action is None:
        title_clean = " ".join(
            tok for tok in raw[resched_task_m.start(1):resched_task_m.end(1)].strip(" ,.:;!?").split()
            if _tr_lower(tok) not in ("bugünkü", "bugunku", "bugün", "bugun", "yks", "tyt", "ayt", "kpss", "dgs", "lgs")
        )
        gun_offset = 1 if "yar" in resched_task_m.group(2) else 0
        if title_clean:
            actions.append(
                CoachAction(
                    type="reschedule_task",
                    label=f"{sinav} · '{title_clean[:80]}' görevi {'yarına' if gun_offset else 'bugüne'} taşındı",
                    auto_apply=True,
                    payload={"sinav": sinav, "title": title_clean[:120], "gun_offset": gun_offset},
                )
            )
    elif comp_m and deneme_action is None:
        title = raw[comp_m.start(1):comp_m.end(1)].strip(" ,.:;!?")
        title_clean = " ".join(
            tok for tok in title.split()
            if _tr_lower(tok) not in ("bugünkü", "bugunku", "bugün", "bugun", "yks", "tyt", "ayt", "kpss", "dgs", "lgs")
        )
        if title_clean:
            actions.append(
                CoachAction(
                    type="complete_task",
                    label=f"{sinav} · '{title_clean[:80]}' görevi tamamlandı",
                    auto_apply=True,
                    payload={"sinav": sinav, "title": title_clean[:120]},
                )
            )

    # 7) Tekil görev ekleme ("bugüne Türev tekrarı görevi ekle")
    if not plan_days_m and not weekly_plan and deneme_action is None and not comp_m and not del_task_m and not resched_task_m:
        task_m = re.search(
            r"(?:bugüne|bugune|yarına|yarina|planıma|planima)\s+(.{2,80}?)\s*(?:görev(?:i|ini)?\s*)?(?:ekle|koy|yaz)\b",
            q_low,
        )
        if task_m and not re.search(r"soru|tercih|liste|deneme|\bnot\b", task_m.group(1)):
            title = raw[task_m.start(1):task_m.end(1)].strip(" ,.:;!?")
            if len(title) >= 2:
                gun_offset = 1 if ("yarına" in q_low or "yarina" in q_low) else 0
                actions.append(
                    CoachAction(
                        type="add_task",
                        label=f"{'Yarın' if gun_offset else 'Bugün'} için '{title[:80]}' görevi eklendi",
                        auto_apply=True,
                        payload={
                            "sinav": sinav,
                            "title": title[:120],
                            "ders": "",
                            "konu": title[:120],
                            "gun_offset": gun_offset,
                        },
                    )
                )

    # 8) Not tamamlama / silme / ekleme
    del_note_m = re.search(
        r"([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,65}?)\s+not(?:unu|umu|u)?\s*(?:sil|kaldır|kaldir)",
        q_low,
    )
    comp_note_m = None if del_note_m else re.search(
        r"([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,65}?)\s+not(?:unu|umu|u)?\s*(?:tamamla|tamamlandı|tamamlandi|bitir|bitirdim|işaretle|isaretle)",
        q_low,
    )
    if del_note_m and deneme_action is None:
        m_txt = raw[del_note_m.start(1):del_note_m.end(1)].strip(" ,.:;!?")
        if m_txt:
            actions.append(
                CoachAction(
                    type="delete_note",
                    label=f"'{m_txt[:60]}' notu silindi",
                    auto_apply=True,
                    payload={"metin": m_txt[:200]},
                )
            )
    elif comp_note_m and deneme_action is None:
        m_txt = raw[comp_note_m.start(1):comp_note_m.end(1)].strip(" ,.:;!?")
        if m_txt:
            actions.append(
                CoachAction(
                    type="complete_note",
                    label=f"'{m_txt[:60]}' notu tamamlandı",
                    auto_apply=True,
                    payload={"metin": m_txt[:200]},
                )
            )
    else:
        note_m = re.search(
            r"(?:([a-zçğıöşüA-ZÇĞİÖŞÜ\s]{2,25}?)\s+)?not(?:u|umu|lar(?:a|ıma)?)?\s*(?:ekle|kaydet|al|yaz)\s*[:\-]?\s*(.+)$",
            raw,
            re.IGNORECASE,
        )
        if note_m and deneme_action is None:
            ders_raw = (note_m.group(1) or "").strip(" ,.:;!?")
            ders_clean = " ".join(
                t for t in ders_raw.split()
                if _tr_lower(t) not in ("bana", "bugün", "bugun", "yks", "tyt", "ayt", "kpss", "dgs", "lgs", "ders", "bir")
            )
            metin = note_m.group(2).strip(" ,.:;!?\"'")
            if len(metin) >= 3:
                ders_val = _tr_title(ders_clean)[:60] if ders_clean else "Genel"
                actions.append(
                    CoachAction(
                        type="add_note",
                        label=f"{sinav} · {ders_val} notu kaydedildi",
                        auto_apply=True,
                        payload={"sinav": sinav, "ders": ders_val, "metin": metin[:2000]},
                    )
                )

    # 9) Çalışma süresi kaydı ("bugün 90 dakika matematik çalıştım", "2 saat çalıştım")
    has_goal_action = any(a.type in ("set_daily_goal", "create_study_plan") for a in actions)
    if deneme_action is None and not has_goal_action and not re.search(r"hedef|kota|haftada|günde|günlük", q_low):
        min_m = re.search(r"(\d{1,3})\s*(?:dakika|\bdk\b)", q_low)
        hr_m = re.search(r"(\d{1,2})\s*saat", q_low)
        worked_cue = bool(re.search(r"çalıştım|calistim|ders\s+çalış|ekle|kaydet|oturdum", q_low))
        if worked_cue and (min_m or hr_m):
            dakika = int(min_m.group(1)) if min_m else int(hr_m.group(1)) * 60
            dakika = max(5, min(720, dakika))
            m_pos = min_m.start() if min_m else hr_m.start()
            ders_guess = _extract_subject_before_questions(raw, m_pos) or "Genel"
            actions.append(
                CoachAction(
                    type="log_study_time",
                    label=f"{sinav} · {ders_guess}: {dakika} dk çalışma kaydedildi",
                    auto_apply=True,
                    payload={"sinav": sinav, "ders": ders_guess[:60], "dakika": dakika},
                )
            )

    # 10) Profil güncelleme (Profile.tsx ile tam senkron: YKS/KPSS/DGS/LGS/TUS/DUS puan, sıra, OBP, şehir)
    if deneme_action is None:
        prof_sinav = _detect_any_sinav(q_low, user_context, _VALID_PROFILE_SINAV)
        rank_m = (
            re.search(r"(?:hedef\s*)?s(?:ı|i)ra(?:lama)?(?:m)?\s*[:=]?\s*(\d{1,3}(?:\.\d{3}){1,2}|\d{2,7})", q_low)
            or re.search(r"(?:hedef\s*)?s(?:ı|i)ra(?:lama)?(?:m)?\s*[:=]?\s*(\d{1,4})\s*(?:bin|k)\b", q_low)
        )
        score_m = re.search(
            r"(?:(?:yks|kpss|dgs|tus|dus)\s*)?(?:hedef\s*)?puan(?:ım|im)?\s*[:=]?\s*(\d{2,3}(?:[.,]\d{1,2})?)",
            q_low,
        )
        obp_m = re.search(r"(?:\bobp\b|diploma\s+notu(?:m)?)\s*[:=]?\s*(\d{2,3}(?:[.,]\d{1,2})?)", q_low)
        yuz_m = re.search(
            r"(?:lgs\s*)?y(?:ü|u)zdelik(?:\s+dilim(?:im)?)?\s*[:=]?\s*%?\s*(\d{1,2}(?:[.,]\d{1,2})?)"
            r"|%\s*(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:lgs|y(?:ü|u)zdelik)",
            q_low,
        )
        city_m = re.search(
            r"(?:tercih\s*)?(?:ş|s)ehir(?:ler(?:im)?)?\s*[:=]?\s*([a-zçğıöşüA-ZÇĞİÖŞÜ,\s\-]{3,80}?)(?=$|[.;]|(?:\s+(?:olarak|yap|kaydet|güncelle|guncelle)))",
            raw,
            re.IGNORECASE,
        )
        has_prof_update_cue = bool(
            re.search(r"profil|kaydet|güncelle|guncelle|ayarla|olsun|ekle|sıram|sıralamam|puanım|obp|diploma|yüzdelik|şehirler", q_low)
        )
        if has_prof_update_cue and (rank_m or score_m or obp_m or yuz_m or city_m):
            prof_payload: dict = {"sinav": prof_sinav}
            lbl_parts = [prof_sinav]
            if rank_m:
                raw_rank_str = rank_m.group(1)
                if "bin" in rank_m.group(0) or rank_m.group(0).endswith("k"):
                    val = int(raw_rank_str.replace(".", "")) * 1000
                else:
                    val = int(raw_rank_str.replace(".", ""))
                val = max(1, min(3_000_000, val))
                prof_payload["siralama"] = val
                prof_payload["hedef_siralama"] = val
                lbl_parts.append(f"sıra {val:,}".replace(",", "."))
            if score_m:
                val_f = max(10.0, min(600.0, float(score_m.group(1).replace(",", "."))))
                prof_payload["puan"] = val_f
                prof_payload["hedef_puan"] = val_f
                lbl_parts.append(f"puan {val_f:g}")
            if prof_sinav in ("YKS", "DGS"):
                if re.search(r"\bea\b|eşit\s+ağırlık", q_low):
                    prof_payload["puan_turu"] = "EA"
                elif re.search(r"\bsöz\b|sözel", q_low):
                    prof_payload["puan_turu"] = "SÖZ"
                elif prof_sinav == "YKS" and re.search(r"\bdil\b", q_low):
                    prof_payload["puan_turu"] = "DİL"
                elif prof_sinav == "YKS" and re.search(r"\btyt\b", q_low):
                    prof_payload["puan_turu"] = "TYT"
                elif re.search(r"\bsay\b|sayısal", q_low):
                    prof_payload["puan_turu"] = "SAY"
            if prof_sinav == "KPSS":
                if "önlisans" in q_low or "onlisans" in q_low:
                    prof_payload["kpss_duzey"] = "önlisans"
                elif "ortaöğretim" in q_low or "ortaogretim" in q_low:
                    prof_payload["kpss_duzey"] = "ortaöğretim"
            if obp_m:
                raw_obp = float(obp_m.group(1).replace(",", "."))
                obp_norm = raw_obp * 5.0 if 50.0 <= raw_obp <= 100.0 else max(0.0, min(500.0, raw_obp))
                prof_payload["obp"] = round(obp_norm, 2)
                lbl_parts.append(f"OBP {prof_payload['obp']:g}")
            if yuz_m:
                yz = max(0.01, min(100.0, float((yuz_m.group(1) or yuz_m.group(2)).replace(",", "."))))
                prof_payload["lgs_yuzdelik"] = yz
                lbl_parts.append(f"%{yz:g} yüzdelik")
            if city_m:
                sehirler = [
                    c.strip().upper()
                    for c in re.split(r"[,/]+|\bve\b", city_m.group(1), flags=re.IGNORECASE)
                    if len(c.strip()) >= 2
                ][:10]
                if sehirler:
                    prof_payload["sehirler"] = sehirler
                    lbl_parts.append(", ".join(sehirler[:3]))
            if len(prof_payload) > 1:
                actions.append(
                    CoachAction(
                        type="update_profile",
                        label=" · ".join(lbl_parts) + " güncellendi",
                        auto_apply=True,
                        payload=prof_payload,
                    )
                )

    # 11) Tercih listesinden çıkarma / optimal sıralama / karşılaştırma açma
    pref_sinav = _detect_any_sinav(q_low, user_context, _VALID_PREF_SINAV)
    rem_pref_m = re.search(
        r"tercih(?:ler)?(?:im)?(?:den)?\s+(.{2,60}?)\s*(?:sil|çıkar|cikar|kaldır|kaldir)",
        q_low,
    )
    if rem_pref_m:
        q_item = raw[rem_pref_m.start(1):rem_pref_m.end(1)].strip(" ,.:;!?\"'")
        code_m = re.search(r"\b(\d{6,9})\b", q_item)
        actions.append(
            CoachAction(
                type="remove_preference",
                label=f"{pref_sinav} tercihinden '{q_item[:60]}' çıkarıldı",
                auto_apply=True,
                payload={
                    "sinav": pref_sinav,
                    **({"code": code_m.group(1)} if code_m else {}),
                    "query": q_item[:80],
                },
            )
        )
    elif re.search(r"(?:tercih(?:ler)?(?:im)?(?:i)?|tercih\s+listem(?:i)?)\s+.*?(?:sırala|sirala|düzenle|duzenle|diz|optimize)", q_low):
        actions.append(
            CoachAction(
                type="reorder_preferences",
                label=f"{pref_sinav} tercih listesi taban sıra/puana göre dizildi",
                auto_apply=True,
                payload={"sinav": pref_sinav, "strategy": "optimal"},
            )
        )

    comp_codes = re.findall(r"\b(\d{9})\b", raw)
    if len(comp_codes) >= 2 and re.search(r"karşılaştır|karsilastir", q_low):
        uniq_cmp = list(dict.fromkeys(comp_codes))[:5]
        actions.append(
            CoachAction(
                type="open_compare",
                label=f"{len(uniq_cmp)} programı karşılaştırma tablosunda aç",
                auto_apply=True,
                payload={"codes": uniq_cmp},
            )
        )

    return actions


def _norm_sinav_code(
    val: object,
    fallback: str = "YKS",
    allowed: tuple[str, ...] = _VALID_SINAV,
) -> str:
    s = str(val or fallback).strip().upper()
    if s in allowed:
        return s
    fb = str(fallback or "YKS").strip().upper()
    return fb if fb in allowed else allowed[0]


def parse_llm_actions_and_strip(raw_text: str, default_sinav: str = "YKS") -> tuple[str, list[CoachAction]]:
    """Gemini cevabındaki <UNISENSE_ACTIONS>[...]</UNISENSE_ACTIONS> bloğunu temizle ve güvenli CoachAction listesi çıkar."""
    if not raw_text:
        return raw_text, []
    parsed_actions: list[CoachAction] = []
    for m in _ACTIONS_TAG_RE.finditer(raw_text):
        blob = m.group(1).strip()
        if not blob:
            continue
        try:
            data = json.loads(blob)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items[:5]:
            if not isinstance(item, dict):
                continue
            atype = str(item.get("type") or "").strip()
            if atype not in _VALID_ACTION_TYPES:
                continue
            raw_payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
            sinav = _norm_sinav_code(
                raw_payload.get("sinav"),
                default_sinav if atype in ("update_profile", "add_preference", "remove_preference", "reorder_preferences") else (default_sinav if default_sinav in _VALID_SINAV else "YKS"),
                allowed=_VALID_PROFILE_SINAV if atype == "update_profile" else (_VALID_PREF_SINAV if atype in ("add_preference", "remove_preference", "reorder_preferences") else _VALID_SINAV),
            )
            payload: dict = {"sinav": sinav}

            if atype == "set_daily_goal":
                if raw_payload.get("gunluk_soru") is not None:
                    try:
                        payload["gunluk_soru"] = max(5, min(1000, int(raw_payload["gunluk_soru"])))
                    except (TypeError, ValueError):
                        pass
                if raw_payload.get("hedef_saat") is not None:
                    try:
                        payload["hedef_saat"] = max(1, min(100, int(raw_payload["hedef_saat"])))
                    except (TypeError, ValueError):
                        pass
                if isinstance(raw_payload.get("hedef_bolum"), str) and raw_payload["hedef_bolum"].strip():
                    payload["hedef_bolum"] = raw_payload["hedef_bolum"].strip()[:120]
            elif atype == "log_questions":
                try:
                    coz = max(1, min(500, int(raw_payload.get("cozulen") or 0)))
                except (TypeError, ValueError):
                    continue
                try:
                    dogru = max(0, min(coz, int(raw_payload.get("dogru", coz))))
                except (TypeError, ValueError):
                    dogru = coz
                payload["ders"] = str(raw_payload.get("ders") or "Genel").strip()[:60] or "Genel"
                payload["konu"] = str(raw_payload.get("konu") or payload["ders"]).strip()[:120]
                payload["cozulen"] = coz
                payload["dogru"] = dogru
            elif atype == "create_study_plan":
                try:
                    gun = max(1, min(365, int(raw_payload.get("gun_sayisi") or 30)))
                except (TypeError, ValueError):
                    gun = 30
                payload["gun_sayisi"] = gun
                if raw_payload.get("gunluk_soru") is not None:
                    try:
                        payload["gunluk_soru"] = max(5, min(1000, int(raw_payload["gunluk_soru"])))
                    except (TypeError, ValueError):
                        pass
            elif atype in ("mark_topic_done", "unmark_topic_done"):
                konu = str(raw_payload.get("konu") or "").strip()[:120]
                if not konu:
                    continue
                payload["konu"] = konu
            elif atype == "add_task":
                title = str(raw_payload.get("title") or "").strip()[:120]
                if not title:
                    continue
                payload["title"] = title
                payload["ders"] = str(raw_payload.get("ders") or "").strip()[:60]
                payload["konu"] = str(raw_payload.get("konu") or title).strip()[:120]
                payload["gun_offset"] = 1 if raw_payload.get("gun_offset") == 1 else 0
            elif atype in ("complete_task", "delete_task"):
                title = str(raw_payload.get("title") or "").strip()[:120]
                if not title:
                    continue
                payload["title"] = title
            elif atype == "reschedule_task":
                title = str(raw_payload.get("title") or "").strip()[:120]
                if not title:
                    continue
                payload["title"] = title
                payload["gun_offset"] = 1 if raw_payload.get("gun_offset") == 1 else 0
            elif atype == "add_note":
                metin = str(raw_payload.get("metin") or "").strip()[:2000]
                if not metin:
                    continue
                payload["ders"] = str(raw_payload.get("ders") or "Genel").strip()[:60] or "Genel"
                payload["metin"] = metin
            elif atype in ("complete_note", "delete_note"):
                metin = str(raw_payload.get("metin") or "").strip()[:200]
                if not metin:
                    continue
                payload["metin"] = metin
            elif atype == "log_study_time":
                try:
                    dk = max(5, min(720, int(raw_payload.get("dakika") or 0)))
                except (TypeError, ValueError):
                    continue
                payload["ders"] = str(raw_payload.get("ders") or "Genel").strip()[:60] or "Genel"
                payload["dakika"] = dk
            elif atype == "update_profile":
                s_raw = raw_payload.get("siralama") if raw_payload.get("siralama") is not None else raw_payload.get("hedef_siralama")
                if s_raw is not None:
                    try:
                        s_val = max(1, min(3_000_000, int(s_raw)))
                        payload["siralama"] = s_val
                        payload["hedef_siralama"] = s_val
                    except (TypeError, ValueError):
                        pass
                p_raw = raw_payload.get("puan") if raw_payload.get("puan") is not None else raw_payload.get("hedef_puan")
                if p_raw is not None:
                    try:
                        p_val = max(10.0, min(600.0, float(p_raw)))
                        payload["puan"] = p_val
                        payload["hedef_puan"] = p_val
                    except (TypeError, ValueError):
                        pass
                if isinstance(raw_payload.get("puan_turu"), str):
                    pt = raw_payload["puan_turu"].strip().upper()
                    pt = {"SOZ": "SÖZ", "DIL": "DİL"}.get(pt, pt)
                    if pt in ("SAY", "EA", "SÖZ", "DİL", "TYT"):
                        payload["puan_turu"] = pt
                if isinstance(raw_payload.get("kpss_duzey"), str):
                    kd = raw_payload["kpss_duzey"].strip().lower()
                    if kd in ("lisans", "önlisans", "ortaöğretim"):
                        payload["kpss_duzey"] = kd
                if raw_payload.get("lgs_yuzdelik") is not None:
                    try:
                        payload["lgs_yuzdelik"] = max(0.01, min(100.0, float(raw_payload["lgs_yuzdelik"])))
                    except (TypeError, ValueError):
                        pass
                if raw_payload.get("obp") is not None:
                    try:
                        raw_obp = float(raw_payload["obp"])
                        payload["obp"] = round(raw_obp * 5.0 if 50.0 <= raw_obp <= 100.0 else max(0.0, min(500.0, raw_obp)), 2)
                    except (TypeError, ValueError):
                        pass
                if raw_payload.get("daily_question_goal") is not None:
                    try:
                        payload["daily_question_goal"] = max(5, min(1000, int(raw_payload["daily_question_goal"])))
                    except (TypeError, ValueError):
                        pass
                if isinstance(raw_payload.get("sehirler"), list):
                    cities = [str(c).strip().upper()[:50] for c in raw_payload["sehirler"] if str(c).strip()][:10]
                    if cities:
                        payload["sehirler"] = cities
                if len(payload) <= 1:
                    continue
            elif atype == "add_deneme":
                raw_girdi = raw_payload.get("girdi")
                if not isinstance(raw_girdi, dict):
                    continue
                clean_girdi: dict[str, dict[str, int]] = {}
                for k, v in raw_girdi.items():
                    fid = _DENEME_FIELD_ALIASES.get(str(k).strip().lower(), str(k).strip().lower())
                    if fid not in _DENEME_FIELD_LIMITS or not isinstance(v, dict):
                        continue
                    lim = _DENEME_FIELD_LIMITS[fid]
                    try:
                        d_val = max(0, min(lim, int(v.get("d", 0))))
                        y_val = max(0, min(lim - d_val, int(v.get("y", 0))))
                    except (TypeError, ValueError):
                        continue
                    clean_girdi[fid] = {"d": d_val, "y": y_val}
                if not clean_girdi:
                    continue
                if sinav in ("YKS", "DGS") and isinstance(raw_payload.get("type"), str):
                    t_up = raw_payload["type"].strip().upper()
                    t_norm = {"SOZ": "SÖZ", "DIL": "DİL"}.get(t_up, t_up)
                    if t_norm in ("TYT", "SAY", "EA", "SÖZ", "DİL"):
                        payload["type"] = t_norm
                elif sinav == "YKS":
                    has_ayt = any(f.startswith("ayt_") for f in clean_girdi)
                    payload["type"] = "SAY" if has_ayt else "TYT"
                elif sinav == "DGS":
                    payload["type"] = "SAY"
                toplam_net, puan = _preview_deneme_metrics(sinav, payload.get("type"), clean_girdi)
                payload["ad"] = str(raw_payload.get("ad") or f"{sinav} Deneme").strip()[:60]
                payload["gun_offset"] = -1 if raw_payload.get("gun_offset") == -1 else 0
                payload["girdi"] = clean_girdi
                payload["toplam_net_preview"] = toplam_net
                payload["puan_preview"] = puan
            elif atype == "add_preference":
                codes = [
                    str(c).strip()
                    for c in (raw_payload.get("codes") or [])
                    if re.fullmatch(r"[A-Za-z0-9._\-]{4,20}", str(c).strip())
                ]
                q_str = str(raw_payload.get("query") or "").strip()[:120]
                if not codes and not q_str:
                    continue
                payload = {"sinav": sinav, "codes": list(dict.fromkeys(codes))[:5]}
                if q_str:
                    payload["query"] = q_str
            elif atype == "remove_preference":
                code = str(raw_payload.get("code") or "").strip()[:20]
                q_str = str(raw_payload.get("query") or "").strip()[:80]
                if not code and not q_str:
                    continue
                payload = {"sinav": sinav}
                if code:
                    payload["code"] = code
                if q_str:
                    payload["query"] = q_str
            elif atype == "reorder_preferences":
                payload = {"sinav": sinav, "strategy": "optimal"}
            elif atype == "open_compare":
                codes = [
                    str(c).strip()
                    for c in (raw_payload.get("codes") or [])
                    if re.fullmatch(r"\d{9}", str(c).strip())
                ]
                if len(codes) < 2:
                    continue
                payload = {"codes": list(dict.fromkeys(codes))[:5]}

            label = str(item.get("label") or f"{atype} uygulandı").strip()[:160]
            parsed_actions.append(CoachAction(type=atype, label=label, auto_apply=True, payload=payload))

    cleaned_text = _ACTIONS_TAG_RE.sub("", raw_text).strip()
    return cleaned_text, parsed_actions


def merge_coach_actions(
    det_actions: list[CoachAction],
    llm_actions: list[CoachAction],
) -> list[CoachAction]:
    """Deterministik ve Gemini üretimi aksiyonları tip çakışması olmadan birleştir."""
    if not llm_actions:
        return list(det_actions)
    if not det_actions:
        return list(llm_actions)

    merged: list[CoachAction] = []
    seen_types: set[str] = set()
    pref_groups: dict[str, dict] = {}
    has_deneme = any(a.type == "add_deneme" for a in (*det_actions, *llm_actions))

    for a in [*det_actions, *llm_actions]:
        if a.type == "log_questions" and has_deneme:
            continue
        if a.type == "add_preference":
            p = a.payload or {}
            s_key = str(p.get("sinav") or "YKS").upper()
            grp = pref_groups.setdefault(s_key, {"codes": [], "query": ""})
            grp["codes"].extend(str(c) for c in (p.get("codes") or []) if c)
            if p.get("query") and not grp["query"]:
                grp["query"] = str(p["query"])
            continue
        if a.type not in seen_types:
            seen_types.add(a.type)
            merged.append(a)

    for s_key, grp in pref_groups.items():
        uniq_codes = list(dict.fromkeys(grp["codes"]))[:5]
        q_val = grp["query"]
        if uniq_codes or q_val:
            payload: dict = {"sinav": s_key, "codes": uniq_codes}
            if q_val:
                payload["query"] = q_val
            lbl = (
                f"{s_key} · {len(uniq_codes)} program tercih listene eklendi"
                if uniq_codes
                else f"{s_key} · '{q_val[:40]}' tercih listene eklendi"
            )
            merged.append(
                CoachAction(
                    type="add_preference",
                    label=lbl,
                    auto_apply=True,
                    payload=payload,
                )
            )
    return merged


def build_coach_action_context(
    actions: list[CoachAction],
    user_context: dict | None = None,
    *,
    pref_intent: bool = False,
    history_codes: list[str] | None = None,
) -> str:
    """LLM'in hangi sistem işleminin tetiklendiğini ve geçmiş tercih kodlarını bilmesi için kısa bağlam üret."""
    if not actions and not pref_intent:
        return ""
    lines = ["=== SİSTEM AKSİYON DURUMU ==="]
    for a in actions:
        lines.append(f"- [Uygulandı: {a.type}] {a.label}")
        if a.type == "add_deneme":
            girdi = (a.payload or {}).get("girdi") or {}
            detay = []
            pen = (1.0 / 3.0) if (a.payload or {}).get("sinav") == "LGS" else 0.25
            for fid, dy in girdi.items():
                d_val = dy.get("d", 0)
                y_val = dy.get("y", 0)
                net = d_val - pen * y_val
                fname = _DENEME_FIELD_LABELS.get(fid, fid)
                detay.append(f"{fname}: {d_val}D {y_val}Y ({net:g} net)")
            if detay:
                lines.append("  • Ders kırılımı: " + ", ".join(detay))
            lines.append(
                f"  • Toplam Net: {(a.payload or {}).get('toplam_net_preview', 0):g}"
                + (f", Tahmini Puan: {(a.payload or {}).get('puan_preview', 0):g}" if (a.payload or {}).get("puan_preview") else "")
            )
    if pref_intent:
        lines.append("- Kullanıcı tercih listesine bölüm eklemek istiyor.")
        if history_codes:
            lines.append("- Önceki mesajlarda geçen ÖSYM kodları: " + ", ".join(history_codes[:5]))
        lines.append("- İlgili geçerli 9 haneli ÖSYM kodunu kullanarak add_preference aksiyonu üret.")
    if user_context:
        hedef = user_context.get("gunluk_soru_hedef")
        bugun = user_context.get("bugun_cozulen_soru")
        if hedef is not None:
            lines.append(f"- Öğrencinin günlük soru hedefi: {hedef} (bugün çözülen: {bugun or 0})")
    lines.append("Sistem öğrenci hesabına yazma yetkisine sahiptir; kullanıcıyı net ve motive edici şekilde teyit et.")
    return "\n".join(lines)


def fallback_coach_reply(actions: list[CoachAction]) -> str:
    """LLM geçici olarak erişilemese bile uygulanan sistem aksiyonunu temiz Türkçe ile bildir."""
    if not actions:
        return "⚠️ Şu an cevap üretemedim, lütfen birazdan tekrar dene."
    bullets = "\n".join(f"• ✅ {a.label}" for a in actions)
    return f"Sistemin güncellendi:\n{bullets}\n\nDevam etmek için yeni soru veya komut yazabilirsin."
