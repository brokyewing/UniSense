"""Input sanitizer — prompt injection defense."""
from __future__ import annotations

import re
import unicodedata

from unisense.domain.exceptions import PromptInjectionError, ValidationError

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?)",
    r"(disregard|forget|override)\s+(your\s+)?(instructions?|rules?|guidelines?)",
    r"you\s+are\s+now\s+(a\s+)?(\w+\s+){0,3}(jailbroken|free|unlimited)",
    r"\bDAN\b\s*(mode|prompt)",
    r"developer\s+mode\s+(enabled|on)",
    r"system\s*[:=]\s*[\"']",
    r"<\|\s*im_start\s*\|>",
    r"</?(system|assistant|user)>",
    r"###\s*(system|instruction)\s*:",
    r"önceki\s+(tüm\s+)?(talimatları|kuralları)\s+(yok\s+say|unut|geçersiz\s+kıl)",
    r"sistem\s+prompt['\"]u\s+(göster|yazdır|söyle)",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_QUERY_LENGTH = 500


def sanitize_query(text: str) -> str:
    if not text or not text.strip():
        raise ValidationError("Sorgu boş olamaz")
    text = unicodedata.normalize("NFKC", text)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = " ".join(text.split())
    if len(text) > MAX_QUERY_LENGTH:
        raise ValidationError(
            f"Sorgu çok uzun (max {MAX_QUERY_LENGTH} karakter)",
            details={"length": len(text), "max": MAX_QUERY_LENGTH},
        )
    if _INJECTION_RE.search(text):
        raise PromptInjectionError(
            "Şüpheli prompt yapısı algılandı",
            details={"text_preview": text[:100]},
        )
    return text
