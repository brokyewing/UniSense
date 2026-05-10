"""Multi-LLM Router — Gemini ile UniSenseLocal arasında geçiş yapan provider."""
from __future__ import annotations

from unisense.application.interfaces.llm_provider import LLMProvider
from unisense.core.logging import get_logger
from unisense.domain.exceptions import UpstreamError

logger = get_logger(__name__)


class MultiLLMRouter:
    """Hangi modeli kullanacağına runtime'da karar veren router.

    Kullanım:
        router = MultiLLMRouter(gemini=GeminiProvider(), qwen=QwenProvider())
        router.generate(query, context, model_preference="gemini")  # default
        router.generate(query, context, model_preference="unisense-local")
    """

    name = "multi-router"

    def __init__(self, gemini: LLMProvider, qwen: LLMProvider) -> None:
        self._providers = {
            "gemini": gemini,
            "unisense-local": qwen,
        }

    def is_available(self) -> bool:
        return any(p.is_available() for p in self._providers.values())

    def get_available_models(self) -> list[dict]:
        """Frontend için: hangi modeller şu an çalışıyor?"""
        return [
            {
                "id": key,
                "name": "Gemini" if key == "gemini" else "UniSenseLocal",
                "available": p.is_available(),
                "description": (
                    "Google Gemini Flash Lite — bulut, hızlı, geniş bilgi"
                    if key == "gemini"
                    else "Yerel Qwen3-4B (UniSense'e fine-tuned) — hızlı, gizli, quotasız"
                ),
            }
            for key, p in self._providers.items()
        ]

    def generate(
        self,
        query: str,
        context: str | None = None,
        history: list[dict] | None = None,
        model_preference: str = "gemini",
    ) -> str:
        """Tercih edilen modele git, başarısız olursa diğerine düş."""
        primary_key = model_preference if model_preference in self._providers else "gemini"
        primary = self._providers[primary_key]
        fallback_key = "unisense-local" if primary_key == "gemini" else "gemini"
        fallback = self._providers[fallback_key]

        # 1. Tercih edilen modeli dene
        if primary.is_available():
            try:
                logger.info("llm_route", model=primary_key)
                return primary.generate(query, context=context, history=history)
            except UpstreamError as e:
                logger.warning("primary_failed", model=primary_key, error=str(e)[:120])

        # 2. Fallback dene
        if fallback.is_available():
            try:
                logger.info("llm_fallback", model=fallback_key)
                resp = fallback.generate(query, context=context, history=history)
                return f"[{fallback_key}'a fallback] {resp}"
            except UpstreamError as e:
                logger.warning("fallback_failed", model=fallback_key, error=str(e)[:120])

        # 3. İkisi de fail
        raise UpstreamError(
            f"Hiçbir LLM kullanılamıyor. "
            f"Gemini quota mı? UniSenseLocal (Ollama) çalışıyor mu?"
        )
