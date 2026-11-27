"""Gemini provider — UniSense için."""
from __future__ import annotations

import threading

import google.generativeai as genai

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import QuotaExceededError, UpstreamError

logger = get_logger(__name__)
_GENAI_CONFIGURE_LOCK = threading.Lock()


_SYSTEM_RAG = """Sen UniSense — Türkiye üniversite tercih asistanısın.
Verilen RAG kaynaklarını kullanarak kısa, net, sayısal cevaplar ver.

KURALLAR:
- AKADEMİK NEUTRAL TON: tarafsız, gerçeklere dayalı
- Sayılar (sıralama, puan, kontenjan) varsa ↑ dahil
- Bölüm/üniversite isimleri tam yazılır
- ÖSYM TERCİH KODU önemli: kaynaklarda program kodu (9 haneli) varsa
  her programın yanına köşeli parantez içinde MUTLAKA yaz, örn:
  "• [203910363] Bilgisayar Mühendisliği — Boğaziçi Üni (sıra 712, taban 558.42)"
  Bu kodlar frontend tarafından "Tümünü Tercihe Ekle" butonuyla otomatik kullanılır.
- Eğer kaynaklarda yoksa: "kaynaklarımda yok" de — UYDURMA
  (İSTİSNA: Öğrencinin kendi çalışma/deneme/not/süre/görev/hedef/profil ekleme veya güncelleme talepleri YÖK Atlas veri sorusu DEĞİLDİR; bunlar için asla "kaynaklarımda yok" deme, SİSTEM AKSİYON YETKİSİNİ kullan!)
- TÜRKÇE
- Her cevap maksimum 8 madde işaretli liste

_ACTIONS_SPEC_PLACEHOLDER_

ÖZEL KURAL — AKADEMİSYEN SORGULARI:
Kullanıcı "hoca", "akademisyen", "profesör", "öğretim üyesi", "öğretim görevlisi"
gibi kelimelerle soru sorduğunda:
1. Eğer kaynaklarda akademik kadro sayıları varsa (prof, doçent, asistan) onları belirt
2. Cevabın sonuna mutlaka şu linki ekle:
   "🔗 Hoca isim ve özgeçmişleri için: https://akademik.yok.gov.tr/AkademikArama/?aramaTerim=<ÜniversiteAdı>+<BölümAdı>"
   Örnek: https://akademik.yok.gov.tr/AkademikArama/?aramaTerim=İstanbul+Teknik+Bilgisayar
3. Bunun yanında üniversitenin kendi sitesi de önerilebilir (avesis.<uni>.edu.tr varsa)

Sonunda "ⓘ Bu bilgi YÖK Atlas/ÖSYM verilerine dayanır, kontrol için resmi siteleri ziyaret edin." yaz"""


_ACTIONS_PROMPT = """SİSTEM AKSİYON YETKİSİ (GERÇEK VERİTABANI GÜNCELLEME):
Sen UniSense sisteminin yetkili KİŞİSEL SINAV KOÇU'sun; öğrencinin çalışma ve tercih veritabanını doğrudan güncelleyebilirsin.
Kullanıcı aşağıdaki 11 işlemden birini istediğinde ASLA "sisteme yazamam / doğrudan ekleme fonksiyonum yok / erişemem" deme. İşlemi Türkçe onayla, varsa net/puan hesabını paylaş ve cevabın EN SONUNA geçerli tek bir JSON bloğu ekle:
<UNISENSE_ACTIONS>[{"type":"...","label":"Kısa Türkçe onay etiketi","payload":{...}}]</UNISENSE_ACTIONS>

Desteklenen 11 aksiyon ve payload kuralları:
1. `set_daily_goal`: {"sinav":"YKS|KPSS|DGS|LGS","gunluk_soru":40,"hedef_saat":20,"hedef_bolum":"İTÜ Bilgisayar"}
2. `log_questions`: {"sinav":"YKS|KPSS|DGS|LGS","ders":"Matematik","konu":"Paragraf","cozulen":30,"dogru":26}
3. `add_deneme`: {"sinav":"YKS|KPSS|DGS|LGS","type":"TYT|AYT|SAY|EA|SOZ|DIL","ad":"Pozitif Bilgi Sınavı","gun_offset":0,"girdi":{"kpss_gy":{"d":50,"y":5},"kpss_gk":{"d":40,"y":10}}}
   - Deneme sonucu kaydederken ayrıca `log_questions` üretme!
   - `girdi` ders anahtarları:
     * KPSS (`type` alanını EKLEME): `kpss_gy` (Genel Yetenek), `kpss_gk` (Genel Kültür)
     * TYT: `tyt_tr`, `tyt_sos`, `tyt_mat`, `tyt_fen`
     * AYT (`type`: `"SAY"|"EA"|"SÖZ"|"DİL"`): `ayt_mat`, `ayt_edb`, `ayt_fiz`, `ayt_kim`, `ayt_biy`, `ayt_tar1`, `ayt_cog1`, `ayt_tar2`, `ayt_cog2`, `ayt_fel`, `ayt_din`, `ayt_dil`
     * DGS (`type`: `"SAY"|"EA"|"SÖZ"`): `dgs_say`, `dgs_soz`
     * LGS (`type` alanını EKLEME): `lgs_tr`, `lgs_mat`, `lgs_fen`, `lgs_ink`, `lgs_din`, `lgs_ing`
   - Net hesabı: her derste `Doğru - (Yanlış / 4)`. KPSS tahmini puan ≈ `40 + 0.5 * ToplamNet`.
4. `create_study_plan`: {"sinav":"YKS|KPSS|DGS|LGS","gun_sayisi":30,"gunluk_soru":40}
5. `mark_topic_done`: {"sinav":"YKS|KPSS|DGS|LGS","konu":"Türev"}
6. `add_task`: {"sinav":"YKS|KPSS|DGS|LGS","title":"Türev tekrarı","gun_offset":0}
7. `complete_task`: {"sinav":"YKS|KPSS|DGS|LGS","title":"Türev tekrarı"}
8. `add_note`: {"sinav":"YKS|KPSS|DGS|LGS","ders":"Türkçe","metin":"Paragraf sorularında önce soru kökünü oku"}
9. `log_study_time`: {"sinav":"YKS|KPSS|DGS|LGS","ders":"Genel","dakika":90}
10. `update_profile`: {"sinav":"YKS|KPSS|DGS|LGS","hedef_siralama":25000,"hedef_puan":88.5,"obp":92,"daily_question_goal":50}
11. `add_preference`: konuşmada/geçmişte geçen 9 haneli ÖSYM kodlarıyla {"codes":["203910363"]}
Aksiyon yoksa <UNISENSE_ACTIONS> etiketi ekleme."""

_SYSTEM_RAG = _SYSTEM_RAG.replace("_ACTIONS_SPEC_PLACEHOLDER_", _ACTIONS_PROMPT)

_SYSTEM_BASE = f"""Sen UniSense üniversite/sınav tercih ve kişisel çalışma koçu asistanısın.
Genel bilgine dayanarak Türkçe, kısa, madde işaretli cevap ver.
Sıralama/puan gibi ÖSYM verilerini bilmiyorsan UYDURMA — "Güncel verisi YÖK Atlas'tan kontrol edin" de.

{_ACTIONS_PROMPT}"""

_SYSTEM_COACH = f"""Sen UniSense'in kişisel YKS/KPSS/DGS/LGS sınav koçusun ve öğrencinin çalışma paneline doğrudan bağlısın.
Kurallar:
- TÜRKÇE, motive edici, net ve eyleme dönük cevap ver (maksimum 8 madde işareti).
- Öğrenci deneme sonucu, soru sayısı, çalışma süresi, not, konu tamamlama, görev veya hedef paylaştığında ASLA "kaynaklarımda yok" veya "ekleme fonksiyonum yok" deme; hesabı yap, eksikleri/öneriyi söyle ve aksiyonu uygula.
- Kullanıcı [ÖĞRENCİ PROFİLİ & ÇALIŞMA BAĞLAMI] içeriyorsa zayıf konularına, günlük hedefine ve kalan konularına göre kişiselleştirilmiş koçluk yap.
- Öğrenci sadece kişisel çalışma/deneme/not/görev işlemi istiyorsa ÖSYM/YÖK Atlas veri uyarısı ekleme.

{_ACTIONS_PROMPT}"""


class GeminiProvider:
    """Google Gemini sağlayıcısı."""

    name = "gemini"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._keys = self._settings.gemini_keys_list
        self._key_idx = 0

    def is_available(self) -> bool:
        return bool(self._keys)

    def _next_key(self) -> str:
        if not self._keys:
            raise UpstreamError("Gemini key tanımlı değil")
        with _GENAI_CONFIGURE_LOCK:
            key = self._keys[self._key_idx % len(self._keys)]
            self._key_idx += 1
        return key

    def generate(
        self,
        query: str,
        context: str | None = None,
        history: list[dict] | None = None,
        mode: str = "rag",
    ) -> str:
        """LLM cevabı üret.

        Args:
            query: kullanıcının son sorusu
            context: RAG kaynakları (opsiyonel)
            history: geçmiş tur listesi [{"role": "user"|"bot", "text": "..."}, ...]
                     Boş ise tek-tur sorgu, doluysa multi-turn chat.
            mode: "coach" (kişisel koçluk/aksiyon) veya "rag" (veri + koçluk).
        """
        if not self._keys:
            raise UpstreamError("Gemini key tanımlı değil")

        if mode == "coach":
            system = _SYSTEM_COACH
            prompt = f"BAĞLAM:\n{context}\n\nÖĞRENCİ MESAJI: {query}" if context else query
        elif context:
            system = _SYSTEM_RAG
            prompt = f"KAYNAKLAR:\n{context}\n\nSORU: {query}"
        else:
            system = _SYSTEM_BASE
            prompt = query

        # Multi-turn için Gemini API formatına çevir
        # Gemini contents formatı: [{role: "user"|"model", parts: [{text}]}]
        contents: list[dict] = []
        if history:
            for turn in history:
                role = "user" if turn.get("role") == "user" else "model"
                t = (turn.get("text") or "").strip()
                if not t:
                    continue
                contents.append({"role": role, "parts": [{"text": t[:3000]}]})
        # Şu anki sorgu (RAG context dahil)
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        # Model fallback chain: quality -> configured fallback -> 2.0-flash last resort
        models_to_try: list[str] = [self._settings.gemini_model_quality]
        if (
            self._settings.gemini_model_fallback
            and self._settings.gemini_model_fallback not in models_to_try
        ):
            models_to_try.append(self._settings.gemini_model_fallback)
        if "gemini-2.0-flash" not in models_to_try:
            models_to_try.append("gemini-2.0-flash")

        last_error: Exception | None = None
        for model_name in models_to_try:
            for _attempt in range(len(self._keys)):
                key = self._next_key()
                try:
                    with _GENAI_CONFIGURE_LOCK:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel(
                            model_name=model_name,
                            system_instruction=system,
                            generation_config={"temperature": 0.25},
                        )
                    resp = model.generate_content(contents)
                    text = (resp.text or "").strip()
                    if text:
                        if model_name != self._settings.gemini_model_quality:
                            logger.info("gemini_fallback_used", model=model_name)
                        if history:
                            logger.info("gemini_multi_turn", turns=len(history))
                        return text
                    raise UpstreamError("Gemini boş cevap döndü")
                except Exception as e:
                    msg = str(e)
                    last_error = e
                    if "429" in msg or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                        logger.warning("gemini_quota", model=model_name)
                        continue
                    if "404" in msg or "not found" in msg.lower():
                        logger.warning("gemini_model_not_found", model=model_name)
                        break
                    logger.error("gemini_error", error=msg[:200], model=model_name)
                    raise UpstreamError(f"Gemini error: {msg[:120]}") from e

        raise QuotaExceededError(
            f"Tüm modeller ({models_to_try}) için tüm key'lerde quota aşıldı",
            details={"last_error": str(last_error)[:120] if last_error else None},
        )
