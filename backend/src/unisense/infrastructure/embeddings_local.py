"""Lokal statik embedding — korpusa özel kelime tablosu (Model2Vec tekniği).

512MB'lık free instance gerçeği:
- Transformer ONNX (MiniLM int8): yüklenince ~415MB → sığmadı
- Hazır statik model (potion, 500k vocab): tokenizer'ı ~400MB → sığmadı
Bu yüzden sözlük korpustan damıtıldı (scripts/build_static_model.py):
~60-80k Türkçe kelime, her biri MiniLM ile embed'lenmiş, int8 tablo.
Runtime: saf numpy + dict lookup → ~50MB RAM, <1ms sorgu.

Embedding = kelimelerin idf-ağırlıklı ortalaması, L2 normalize.
Sözlük dışı kelimeler atlanır (hibrit retrieval'daki keyword bacağı ve
yapısal sorgu yönlendirmesi bu boşluğu kapatır).
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)

# build_static_model.py ile AYNI tokenizasyon olmak ZORUNDA
_WORD_RE = re.compile(r"[a-zçğıöşü]+", re.IGNORECASE)


def _tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(_tr_lower(text))


def _model_path() -> Path:
    # Model dosyası chroma dizininin yanında durur (birlikte indirilirler):
    # data/embeddings/chromadb + data/embeddings/static_model.npz
    return Path(os.path.abspath(get_settings().chroma_persist_dir)).parent / "static_model.npz"


@lru_cache(maxsize=1)
def _load_model():
    path = _model_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Statik embedding modeli yok: {path} — "
            "scripts/build_static_model.py çalıştır (veya HF dataset'ten indir)"
        )
    logger.info("loading_static_model", path=str(path))
    data = np.load(path)
    table = data["table"]                        # int8 (V, dim)
    scales = data["scales"].astype(np.float32)   # (V,)
    weights = data["weights"].astype(np.float32) # (V,) idf
    vocab = data["vocab"].tolist()
    word_to_id = {w: i for i, w in enumerate(vocab)}
    # ASCII-yazım toleransı: "tip" → "tıp" satırına düşsün. Fold çakışmasında
    # ilk (alfabetik) kelime kazanır — retrieval için kabul edilebilir.
    from unisense.core.text import fold_tr

    fold_to_id: dict[str, int] = {}
    for w, i in word_to_id.items():
        fold_to_id.setdefault(fold_tr(w), i)
    logger.info("static_model_ready", vocab=table.shape[0], dim=table.shape[1])
    return table, scales, weights, word_to_id, fold_to_id


def embed_texts_local(texts: list[str]) -> np.ndarray:
    """Metinleri statik tabloyla embed eder (normalize float32)."""
    from unisense.core.text import fold_tr

    table, scales, weights, word_to_id, fold_to_id = _load_model()
    dim = table.shape[1]

    out = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        ids = []
        for w in _tokenize(text or ""):
            wid = word_to_id.get(w)
            if wid is None:
                wid = fold_to_id.get(fold_tr(w))  # ASCII yazım fallback'i
            if wid is not None:
                ids.append(wid)
        if not ids:
            continue
        idx = np.array(ids, dtype=np.int64)
        rows = table[idx].astype(np.float32) * scales[idx][:, None]
        w = weights[idx][:, None]
        out[i] = (rows * w).sum(axis=0) / (w.sum() + 1e-9)

    norms = np.linalg.norm(out, axis=1, keepdims=True) + 1e-9
    return (out / norms).astype(np.float32)
