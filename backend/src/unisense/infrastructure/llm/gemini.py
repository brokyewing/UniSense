"""Gemini provider — UniSense için."""
from __future__ import annotations

import google.generativeai as genai

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import QuotaExceededError, UpstreamError

logger = get_logger(__name__)


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
- TÜRKÇE
- Her cevap maksimum 8 madde işaretli liste

ÖZEL KURAL — AKADEMİSYEN SORGULARI:
Kullanıcı "hoca", "akademisyen", "profesör", "öğretim üyesi", "öğretim görevlisi"
gibi kelimelerle soru sorduğunda:
1. Eğer kaynaklarda akademik kadro sayıları varsa (prof, doçent, asistan) onları belirt
2. Cevabın sonuna mutlaka şu linki ekle:
   "🔗 Hoca isim ve özgeçmişleri için: https://akademik.yok.gov.tr/AkademikArama/?aramaTerim=<ÜniversiteAdı>+<BölümAdı>"
   Örnek: https://akademik.yok.gov.tr/AkademikArama/?aramaTerim=İstanbul+Teknik+Bilgisayar
3. Bunun yanında üniversitenin kendi sitesi de önerilebilir (avesis.<uni>.edu.tr varsa)

Sonunda "ⓘ Bu bilgi YÖK Atlas/ÖSYM verilerine dayanır, kontrol için resmi siteleri ziyaret edin." yaz"""


_SYSTEM_BASE = """Sen üniversite tercihine yardımcı asistan.
Genel bilgine dayanarak Türkçe, kısa, madde işaretli cevap ver.
Sıralama/puan gibi sayılar bilmiyorsan UYDURMA — "Güncel verisi YÖK Atlas'tan kontrol edin" de."""


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
        key = self._keys[self._key_idx % len(self._keys)]
        self._key_idx += 1
        return key

    def generate(
        self,
        query: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> str:
        """LLM cevabı üret.

        Args:
            query: kullanıcının son sorusu
            context: RAG kaynakları (opsiyonel)
            history: geçmiş tur listesi [{"role": "user"|"bot", "text": "..."}, ...]
                     Boş ise tek-tur sorgu, doluysa multi-turn chat.
        """
        if not self._keys:
            raise UpstreamError("Gemini key tanımlı değil")

        system = _SYSTEM_RAG if context else _SYSTEM_BASE
        prompt = f"KAYNAKLAR:\n{context}\n\nSORU: {query}" if context else query

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

        # Model fallback chain
        models_to_try: list[str] = [self._settings.gemini_model_quality]
        if self._settings.gemini_model_fallback and self._settings.gemini_model_fallback != self._settings.gemini_model_quality:
            models_to_try.append(self._settings.gemini_model_fallback)

        last_error: Exception | None = None
        for model_name in models_to_try:
            for _attempt in range(len(self._keys)):
                key = self._next_key()
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=system)
                    resp = model.generate_content(contents)
                    text = (resp.text or "").strip()
                    if text:
                        if model_name != self._settings.gemini_model_quality:
                            logger.info("gemini_fallback_used", model=model_name)
                        if history:
                            logger.info("gemini_multi_turn", turns=len(history))
                        return text
                    raise UpstreamError("Gemini boş cevap döndü")
                except Exception as e:  # noqa: BLE001
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
