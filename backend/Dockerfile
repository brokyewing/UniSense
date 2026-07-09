FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Sistem bağımlılıkları (chromadb, lxml, sentence-transformers için)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libxml2-dev \
        libxslt1-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bağımlılıkları ÖNCE kur — kod değişince bu katman cache'den gelir
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Kaynak kodu kopyala ve paketi bağımlılıksız kur (deps yukarıda kuruldu)
COPY src ./src
COPY scripts ./scripts
RUN pip install -e . --no-deps

# ONNX embedding modelini imaja göm (~120MB) — cold start'ta indirme olmasın
RUN python -c "from huggingface_hub import hf_hub_download; \
    hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quint8_avx2.onnx'); \
    hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json')"

# Veriyi container'a kopyala. HF Space build context'inde data/embeddings
# (hazır index) de bulunur ve birlikte kopyalanır; GitHub/Render context'inde
# o klasör yoktur, embed ilk boot'ta çalışır.
COPY data ./data

# Non-root kullanıcı — container escape yüzeyini daraltır.
# /data mount noktası da app kullanıcısına verilir; Render diski mount
# ettikten sonra yazma hatası görürsen Render docs "disk + non-root user"
# bölümüne bak (gerekirse bu iki satırı kaldır).
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/chromadb \
    && chown -R app:app /app /data
USER app

# Healthcheck (Render kendi healthCheckPath'ini kullanır; bu local/compose için)
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8002}/api/v1/health || exit 1

ENV APP_PORT=8002
EXPOSE 8002

# İlk boot'ta index boşsa embed çalıştır (idempotent + resume destekli).
# CHROMA_PERSIST_DIR: Render'da /data/chromadb (persistent disk),
# HF Space'te /app/data/embeddings/chromadb (imaja gömülü hazır index).
# --proxy-headers: LB arkasında gerçek istemci IP'si (rate limit için şart)
CMD CHROMA_DIR="${CHROMA_PERSIST_DIR:-/data/chromadb}" && \
    if [ ! -d "$CHROMA_DIR" ] || [ -z "$(ls -A "$CHROMA_DIR" 2>/dev/null)" ]; then \
      echo ">>> ChromaDB empty at $CHROMA_DIR, running embed..." && \
      python -m unisense.cli.embed; \
    fi && \
    exec uvicorn unisense.main:app --host 0.0.0.0 --port ${PORT:-8002} \
      --proxy-headers --forwarded-allow-ips "*"
