"""AI Koç sistem aksiyonları — doğal Türkçe komutları güvenli, şemalı aksiyonlara çevirir."""
from __future__ import annotations

import json
import re

from unisense.domain.models.query import CoachAction

_VALID_SINAV = ("YKS", "KPSS", "DGS", "LGS")
_VALID_ACTION_TYPES = frozenset({
    "set_daily_goal",
    "create_study_plan",
    "log_questions",
    "add_task",
    "mark_topic_done",
    "add_preference",
})
_ACTIONS_TAG_RE = re.compile(r"<UNISENSE_ACTIONS>\s*(.*?)\s*</UNISENSE_ACTIONS>", re.DOTALL | re.IGNORECASE)
_TR_LOWER_MAP = str.maketrans({"İ": "i", "I": "ı"})

_NOISE_WORDS = (
    "bugün", "bugun", "dün", "dun", "yarın", "yarin", "lütfen", "lutfen",
    "bana", "sistemde", "sisteme", "lütfen", "şimdi", "simdi", "ben", "bir",
)


def _tr_lower(text: str) -> str:
    return text.translate(_TR_LOWER_MAP).lower()


def _detect_sinav(q_lower: str, user_context: dict | None = None) -> str:
    if re.search(r"\bkpss\b", q_lower):
        return "KPSS"
    if re.search(r"\bdgs\b", q_lower):
        return "DGS"
    if re.search(r"\blgs\b", q_lower):
        return "LGS"
    if re.search(r"\b(?:yks|tyt|ayt)\b", q_lower):
        return "YKS"
    track = str((user_context or {}).get("exam_track") or "").upper()
    return track if track in _VALID_SINAV else "YKS"


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
    return w[0].upper() + w[1:]


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
            r"(?:hedef|kota|soru|plan|program|bitir|tamamla|işaretle|isaretle|ekle|kaydet|koy|ayarla|olsun|çözdüm|cozdum|yaptım|yaptim|güncelle|guncelle)",
            q_low,
        )
    )


def extract_coach_actions(query_text: str, user_context: dict | None = None) -> list[CoachAction]:
    """Kullanıcı sorgusundan güvenli, şema doğrulamalı sistem aksiyonları çıkar."""
    raw = (query_text or "").strip()
    if not raw:
        return []
    q_low = _tr_lower(raw)
    sinav = _detect_sinav(q_low, user_context)
    actions: list[CoachAction] = []

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
    if q_match and has_log_verb and not is_goal_only:
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
    else:
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

    # 4) Konu tamamlandı işareti ("Türev konusunu bitirdim" / "Paragraf bitti")
    topic_m = re.search(
        r"([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,55}?)\s+konu(?:sunu|nu|yu|su)?\s*(?:bitirdim|tamamladım|tamamladim|işaretle|isaretle|bitti)",
        q_low,
    ) or re.search(
        r"^([a-zçğıöşü0-9][a-zçğıöşü0-9\s\-]{1,45}?)\s+(?:bitirdim|tamamladım|tamamladim|bitti\s*işaretle)$",
        q_low,
    )
    if topic_m and not plan_days_m:
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

    # 5) Tekil görev ekleme ("bugüne Türev tekrarı görevi ekle")
    if not plan_days_m and not weekly_plan:
        task_m = re.search(
            r"(?:bugüne|bugune|yarına|yarina|planıma|planima)\s+(.{2,80}?)\s*(?:görev(?:i|ini)?\s*)?(?:ekle|koy|yaz)\b",
            q_low,
        )
        if task_m and not re.search(r"soru|tercih|liste", task_m.group(1)):
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

    return actions


def _norm_sinav_code(val: object, fallback: str = "YKS") -> str:
    s = str(val or fallback).strip().upper()
    return s if s in _VALID_SINAV else fallback


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
            sinav = _norm_sinav_code(raw_payload.get("sinav"), default_sinav)
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
            elif atype == "mark_topic_done":
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
            elif atype == "add_preference":
                codes = [str(c).strip() for c in (raw_payload.get("codes") or []) if re.fullmatch(r"\d{9}", str(c).strip())]
                if not codes:
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
    pref_codes: list[str] = []

    for a in [*det_actions, *llm_actions]:
        if a.type == "add_preference":
            pref_codes.extend(str(c) for c in (a.payload or {}).get("codes", []) if c)
            continue
        if a.type not in seen_types:
            seen_types.add(a.type)
            merged.append(a)

    if pref_codes:
        uniq_codes = list(dict.fromkeys(pref_codes))[:5]
        merged.append(
            CoachAction(
                type="add_preference",
                label=f"{len(uniq_codes)} programı tercih listene ekle",
                auto_apply=True,
                payload={"codes": uniq_codes},
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
