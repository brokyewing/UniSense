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

# Veriyi container'a kopyala (raw + processed + chunks)
# Veri dosyaları normal git blob'u (LFS değil) — doğrudan kopyalanır.
# embeddings/ Render'da persistent disk olarak mount edilir; container'da boş kalır
COPY data/processed ./data/processed
COPY data/raw ./data/raw

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

# İlk boot'ta index boşsa embed çalıştır (idempotent), sonra uvicorn.
# --proxy-headers: Render LB arkasında gerçek istemci IP'si (rate limit için şart)
CMD if [ ! -d "/data/chromadb" ] || [ -z "$(ls -A /data/chromadb 2>/dev/null)" ]; then \
      echo ">>> ChromaDB empty, running embed..." && \
      python -m unisense.cli.embed; \
    fi && \
    exec uvicorn unisense.main:app --host 0.0.0.0 --port ${PORT:-8002} \
      --proxy-headers --forwarded-allow-ips "*"
