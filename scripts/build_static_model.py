"""Korpusa özel statik embedding modeli damıtır (tek seferlik, lokal).

Neden bu yaklaşım? 512MB'lık free instance'ta:
- Transformer ONNX (MiniLM int8): yüklenince ~415MB — sığmıyor
- Hazır statik model (potion): tablo int8 130MB ama 500k'lık tokenizer'ı
  `tokenizers` kütüphanesinde ~400MB açılıyor — sığmıyor
Çözüm: sözlüğü KORPUSTAN çıkar (~60-80k Türkçe kelime), her kelimeyi
MiniLM'le embed'le (Model2Vec tekniği), int8 sakla. Runtime: numpy dict
lookup — ~50MB RAM, <1ms sorgu, ek kütüphane yok.

Çıktı: backend/data/embeddings/static_model.npz
  (tablo int8 + satır ölçekleri + idf ağırlıkları + kelime listesi)

Gereksinim (sadece build): sentence-transformers (torch) kurulu lokal makine.
Kullanım: python scripts/build_static_model.py
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "backend" / "data" / "embeddings" / "static_model.npz"
CHUNKS = ROOT / "backend" / "data" / "processed" / "chunks.json"

BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MIN_FREQ = 2          # korpusta en az bu kadar geçen kelimeler
MAX_VOCAB = 100_000   # emniyet tavanı
_WORD_RE = re.compile(r"[a-zçğıöşü]+", re.IGNORECASE)


def tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


def tokenize(text: str) -> list[str]:
    """Runtime ile AYNI tokenizasyon (embeddings_local.py bunu kopyalar)."""
    return _WORD_RE.findall(tr_lower(text))


def main() -> None:
    from sentence_transformers import SentenceTransformer

    print("📥 Korpus okunuyor...")
    chunks = json.load(open(CHUNKS, encoding="utf-8"))
    freq: Counter[str] = Counter()
    for c in chunks:
        freq.update(tokenize(c["content"]))

    # Tipik sorgu kelimeleri de sözlükte olsun (korpusta seyrek olabilirler)
    extra = tokenize(
        "hangi nerede kaç puanla girerim istiyorum seviyorum okumak bölümü "
        "üniversiteleri sıralamayla yerleşirim önerir misin tavsiye kolay zor "
        "iyi kötü güzel gelecek maaş iş imkanı"
    )
    for w in extra:
        freq[w] += MIN_FREQ

    corpus_vocab = {w for w, f in freq.items() if f >= MIN_FREQ and len(w) > 1}
    print(f"   korpus sözlüğü: {len(corpus_vocab):,} kelime")

    # Genel Türkçe kelimeler: kullanıcı sorgularındaki eşanlamlılar
    # ("doktorluk" → "tıp" köprüsü) için — MiniLM uzayında yakın düşerler.
    # Kaynak: OpenSubtitles frekans listesi (hermitdave/FrequencyWords)
    print("📥 Genel Türkçe kelime listesi indiriliyor...")
    import urllib.request
    url = ("https://raw.githubusercontent.com/hermitdave/FrequencyWords/"
           "master/content/2018/tr/tr_50k.txt")
    general: list[tuple[str, int]] = []
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            for line in r.read().decode("utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2 and _WORD_RE.fullmatch(parts[0]) and len(parts[0]) > 1:
                    general.append((parts[0], int(parts[1])))
    except Exception as e:  # noqa: BLE001
        print(f"   ⚠️ liste alınamadı ({e}) — sadece korpus sözlüğüyle devam")

    for w, f in general[:40_000]:
        if w not in corpus_vocab:
            corpus_vocab.add(w)
            # Genel-frekansı korpus ölçeğine kabaca indirgeyip idf'e kat
            freq[w] = max(MIN_FREQ, f // 1000)

    vocab = sorted(corpus_vocab)[:MAX_VOCAB]
    print(f"   toplam sözlük: {len(vocab):,} kelime")

    print(f"🧠 {BASE_MODEL} ile kelime embeddingleri (~5-10 dk)...")
    model = SentenceTransformer(BASE_MODEL)
    embs = model.encode(
        vocab, batch_size=512, convert_to_numpy=True,
        show_progress_bar=True, normalize_embeddings=True,
    ).astype(np.float32)

    # Zipf/idf ağırlığı: sık kelimeler (ve, ile, üniversite...) az bilgi taşır
    total = sum(freq[w] for w in vocab)
    weights = np.array(
        [math.log(total / freq[w]) for w in vocab], dtype=np.float32
    )
    weights /= weights.max()

    # int8 satır quantizasyonu
    scales = np.abs(embs).max(axis=1, keepdims=True) / 127.0 + 1e-12
    table_i8 = np.clip(np.round(embs / scales), -127, 127).astype(np.int8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT,
        table=table_i8,
        scales=scales.astype(np.float16).squeeze(1),
        weights=weights.astype(np.float16),
        vocab=np.array(vocab),
    )
    print(f"✅ {OUT} ({OUT.stat().st_size / 1e6:.0f}MB, dim={embs.shape[1]})")


if __name__ == "__main__":
    main()
