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

# Veriyi container'a kopyala. Statik embedding modeli + hazır index
# HF dataset'ten boot'ta iner (fetch_index) — imaja gömülmez.
COPY data ./data

# BELLEK (512MB instance için kritik): departments.json (54MB) → slim kopya
# (~17MB); fat dosya imajdan silinir, yoksa runtime parse'ı ~400MB tepe
# yapıp OOM'a yol açıyor. Compass bölüm matrisi (npz) repo'dan gelir
# (data/processed/compass_dept_embeddings.npz — statik modelle üretilmiş).
RUN python -m unisense.cli.slim_data \
    && rm data/processed/departments.json

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

# İlk boot'ta index boşsa: önce HF dataset'ten hazır index'i indir
# (HF_INDEX_REPO tanımlıysa, ~30-60sn), o da olmazsa embed çalıştır.
# Render free tier'da kalıcı disk yok — index bu yüzden HF'den gelir.
# --proxy-headers: LB arkasında gerçek istemci IP'si (rate limit için şart)
# Index alınamazsa bile UYGULAMA BAŞLAR (degraded): HF kesintisi tüm siteyi
# öldürmesin — RAG-dışı özellikler (takvim/robotlar/öneri/hesap) chroma'sız
# çalışır, index arka planda (lifespan retry) HF dönünce kendiliğinden iner.
CMD CHROMA_DIR="${CHROMA_PERSIST_DIR:-./data/embeddings/chromadb}" && \
    if [ ! -d "$CHROMA_DIR" ] || [ -z "$(ls -A "$CHROMA_DIR" 2>/dev/null)" ]; then \
      timeout 300 python -m unisense.cli.fetch_index || \
      { echo ">>> Index indirilemedi, embed deneniyor..." && timeout 600 python -m unisense.cli.embed; } || \
      echo ">>> Index alinamadi — DEGRADED modda basliyor (RAG kapali, arka planda tekrar denenecek)"; \
    fi; \
    exec uvicorn unisense.main:app --host 0.0.0.0 --port ${PORT:-8002} \
      --proxy-headers --forwarded-allow-ips "*"
