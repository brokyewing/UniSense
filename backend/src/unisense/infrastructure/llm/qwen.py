"""UniSenseLocal LLM provider — Ollama üzerinden Qwen3-4B fine-tuned modele bağlanır.

Önkoşul:
  1. Kaggle'dan GGUF indir:
       kaggle datasets download -d ibrahimaskeroglu/unisense-tr-gguf -p ./unisense-tr-gguf --unzip
  2. Ollama yükle:
       https://ollama.com/download
  3. Modeli oluştur:
       cd unisense-tr-gguf
       ollama create unisense-local -f Modelfile
  4. Ollama serve (otomatik başlar):
       ollama serve  → http://localhost:11434

Backend bu provider üzerinden kullanır.
"""
from __future__ import annotations

from typing import Any

import httpx

from unisense.application.interfaces.llm_provider import LLMProvider
from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import UpstreamError

logger = get_logger(__name__)


# ⚠️ Sıkı sistem prompt — fine-tuned model RAG-style context'i görmediği için
# çoktan-seçmeli halüsinasyona kayabiliyor. Bunu önle.
_SYSTEM = """Sen UniSense — Türkiye 2025 YKS üniversite tercih asistanısın.

KESİN KURALLAR:
1. Sana verilen "KAYNAK BİLGİ" bölümündeki sayıları/üniversite isimlerini AYNEN kullan, ASLA değiştirme.
2. Cevabını madde işaretli (•) liste formatında yaz, en fazla 5 madde.
3. ASLA çoktan seçmeli soru, "A) B) C)" gibi seçenek listesi, "Doğru cevap nedir?" gibi kendine soru sorma.
4. ASLA "Adım 1, Adım 2, SONUÇ" gibi öğretici/akademik format kullanma.
5. KAYNAK BİLGİ bölümünde bilgi yoksa, kısa cevap: "Bu bilgi YÖK Atlas'tan kontrol edilmeli."
6. Program kodlarını [102210277] formatında yaz.
7. ASLA İngilizce kelime, emoji, motivasyon mesajı kullanma.
8. DİREKT cevap ver, yorumlama veya açıklama yapma."""


def _format_context_as_data_card(context: str, max_len: int = 6000) -> str:
    """RAG context'ini modele 'kaynak veri kartı' gibi sun.

    Model fine-tuning'de "Soru → Cevap" formatına alıştı. Ham context'i
    KAYNAKLAR/SORU şeklinde değil, basit "şu bilgilerden faydalan" şeklinde
    veriyoruz. Çok uzunsa kısalt.
    """
    if not context:
        return ""
    ctx = context.strip()
    if len(ctx) > max_len:
        ctx = ctx[:max_len] + "\n[... daha fazla kaynak var, üst N tanesi gösteriliyor]"
    return ctx


class QwenProvider(LLMProvider):
    """Ollama üzerinden UniSenseLocal (Qwen3-4B fine-tuned) ile konuşan provider."""

    name = "unisense-local"

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = getattr(settings, "qwen_base_url", "http://localhost:11434")
        self._model = getattr(settings, "qwen_model_name", "unisense-local")
        self._timeout = 120  # Lokal CPU/GPU yavaş olabilir
        self._client = httpx.Client(timeout=self._timeout)

    def is_available(self) -> bool:
        """Ollama servisine ping at — model yüklü mü?"""
        try:
            r = self._client.get(f"{self._base_url}/api/tags", timeout=3)
            if r.status_code != 200:
                return False
            tags = r.json().get("models", [])
            return any(m.get("name", "").startswith(self._model) for m in tags)
        except Exception:  # noqa: BLE001
            return False

    def generate(
        self,
        query: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> str:
        # Mesaj listesi
        messages: list[dict[str, Any]] = [{"role": "system", "content": _SYSTEM}]

        # Multi-turn history (son 4 mesaj)
        if history:
            for turn in history[-4:]:
                role = "user" if turn.get("role") == "user" else "assistant"
                t = (turn.get("text") or "").strip()
                if t:
                    messages.append({"role": role, "content": t[:2000]})

        # Context'i kullanıcı mesajının BAŞINA ekle (training'in gördüğü format değil
        # ama anlaşılması en kolay format — kuralları sistem prompt'unda zaten verdik)
        ctx_card = _format_context_as_data_card(context or "")
        if ctx_card:
            user_text = (
                f"--- KAYNAK BİLGİ (YÖK Atlas / ÖSYM 2025) ---\n"
                f"{ctx_card}\n"
                f"--- KAYNAK BİLGİ SONU ---\n\n"
                f"Soru: {query}\n\n"
                f"Yukarıdaki KAYNAK BİLGİ'ye DAYANARAK madde işaretli kısa cevap ver. "
                f"Sayıları AYNEN al, uydurma."
            )
        else:
            user_text = query

        messages.append({"role": "user", "content": user_text})

        # Sampling parametrelerini runtime'da override et — Modelfile'dan
        # bağımsız garanti et. Halüsinasyonu zaptetmek için sıkı sıkı.
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.3,        # düşük → halüsinasyon az
                "top_p": 0.9,
                "top_k": 40,
                "min_p": 0.05,
                "repeat_penalty": 1.18,
                "repeat_last_n": 256,
                "num_predict": 350,
                "num_ctx": 4096,
                "stop": ["<|im_end|>", "<|im_start|>", "Doğru cevap", "Adım 1", "###"],
            },
        }

        try:
            r = self._client.post(f"{self._base_url}/api/chat", json=payload)
            if r.status_code != 200:
                raise UpstreamError(f"Ollama HTTP {r.status_code}: {r.text[:200]}")
            data = r.json()
            text = (data.get("message", {}).get("content") or "").strip()
            if not text:
                raise UpstreamError("UniSenseLocal boş cevap döndü")
            logger.info(
                "qwen_generated",
                model=self._model,
                ctx_len=len(ctx_card),
                resp_len=len(text),
            )
            return text
        except httpx.ConnectError as e:
            raise UpstreamError(
                f"Ollama servisine bağlanamadı ({self._base_url}). "
                f"Çalışıyor mu? `ollama serve` komutunu kontrol et."
            ) from e
        except Exception as e:  # noqa: BLE001
            logger.error("qwen_error", error=str(e)[:200])
            raise UpstreamError(f"UniSenseLocal hata: {str(e)[:120]}") from e

    def __del__(self):
        try:
            self._client.close()
        except Exception:
            pass
