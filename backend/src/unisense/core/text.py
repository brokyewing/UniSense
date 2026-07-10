"""Türkçe metin yardımcıları.

fold_tr: Türkçe-güvenli küçük harf + aksan katlama (ş→s, ı→i, ç→c...).
Kullanıcılar mobil klavyede sık sık ASCII yazar ("cerrahpasa tip") —
sorgu ve veri TARAFININ İKİSİ DE katlanınca "tıp" == "tip" eşleşir.
"""
from __future__ import annotations

_FOLD_MAP = str.maketrans({
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "â": "a", "î": "i", "û": "u",
})


def tr_lower(s: str) -> str:
    """Türkçe-güvenli lowercase (İ→i, I→ı)."""
    return s.replace("İ", "i").replace("I", "ı").lower()


def fold_tr(s: str) -> str:
    """tr_lower + aksanları ASCII'ye katla — yazım varyantlarını eşitler."""
    return tr_lower(s).translate(_FOLD_MAP)
