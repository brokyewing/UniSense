"""Lokal ONNX embedding — torch'suz MiniLM.

sentence-transformers'ın resmi ONNX export'unu (quantize, 118MB) onnxruntime
ile çalıştırır. PyTorch'a kıyasla RAM ~1.3GB → ~300MB. Çıktılar,
sentence-transformers pipeline'ı ile aynı mimari (mean pooling + L2 norm);
index bu dosyayla üretildiği sürece kendi içinde tutarlıdır.

API kotası/bedeli yok — $0 çalışır.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)

_BATCH = 32
_MAX_TOKENS = 128  # modelin eğitildiği maksimum uzunluk


@lru_cache(maxsize=1)
def _session_and_tokenizer():
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    settings = get_settings()
    logger.info(
        "loading_onnx_model",
        repo=settings.embedding_onnx_repo,
        file=settings.embedding_onnx_file,
    )
    onnx_path = hf_hub_download(settings.embedding_onnx_repo, settings.embedding_onnx_file)
    tok_path = hf_hub_download(settings.embedding_onnx_repo, "tokenizer.json")

    tokenizer = Tokenizer.from_file(tok_path)
    pad_id = tokenizer.token_to_id("<pad>") or 0
    tokenizer.enable_truncation(max_length=_MAX_TOKENS)
    tokenizer.enable_padding(pad_id=pad_id, pad_token="<pad>")

    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    input_names = {i.name for i in session.get_inputs()}
    return session, tokenizer, input_names


def embed_texts_local(texts: list[str]) -> np.ndarray:
    """Metinleri lokal ONNX modeliyle embed eder (normalize float32)."""
    session, tokenizer, input_names = _session_and_tokenizer()

    out: list[np.ndarray] = []
    for start in range(0, len(texts), _BATCH):
        batch = [t or " " for t in texts[start:start + _BATCH]]
        enc = tokenizer.encode_batch(batch)
        input_ids = np.array([e.ids for e in enc], dtype=np.int64)
        attention = np.array([e.attention_mask for e in enc], dtype=np.int64)

        feeds = {"input_ids": input_ids, "attention_mask": attention}
        if "token_type_ids" in input_names:
            feeds["token_type_ids"] = np.zeros_like(input_ids)

        hidden = session.run(None, feeds)[0]  # (B, T, H)

        # Mean pooling (attention mask ile) — sentence-transformers ile aynı
        mask = attention[..., None].astype(np.float32)
        summed = (hidden * mask).sum(axis=1)
        counts = np.clip(mask.sum(axis=1), 1e-9, None)
        out.append(summed / counts)

    embs = np.vstack(out)
    norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9
    return (embs / norms).astype(np.float32)
