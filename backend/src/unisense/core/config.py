"""UniSense application config."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Uygulama ===
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    app_host: str = "0.0.0.0"
    app_port: int = 8002
    app_log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # === LLM ===
    gemini_api_keys: str = ""
    gemini_api_key: str = ""
    # Default: Flash Lite ailesi (yüksek free tier — 500 RPD / 250K TPM / 15 RPM)
    # .env içinde GEMINI_MODEL_QUALITY ile override edilebilir
    gemini_model_fast: str = "gemini-2.5-flash-lite"
    gemini_model_quality: str = "gemini-flash-lite-latest"
    # Quota dolunca otomatik fallback için fallback model (opsiyonel)
    gemini_model_fallback: str = "gemini-2.5-flash-lite"

    # === ChromaDB / Embeddings ===
    chroma_persist_dir: str = "./data/embeddings/chromadb"
    chroma_collection: str = "unisense"
    # Sağlayıcı seçimi:
    #   local  → ONNX MiniLM (torch'suz, $0, kota yok) — varsayılan
    #   gemini → Gemini API (daha kaliteli ama index kurulumu billing ister:
    #            free tier günlük istek limiti 24k chunk'a yetmez)
    # DİKKAT: Index hangi sağlayıcıyla üretildiyse sorgular da onunla yapılmalı.
    embedding_provider: str = Field(default="local", pattern="^(local|gemini)$")
    embedding_onnx_repo: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_onnx_file: str = "onnx/model_quint8_avx2.onnx"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    embedding_dim: int = 768  # sadece gemini için; local her zaman 384

    @property
    def effective_embedding_dim(self) -> int:
        return 384 if self.embedding_provider == "local" else self.embedding_dim

    # === Güvenlik ===
    security_require_api_key: bool = False
    security_api_keys: str = ""
    # Firebase ID token doğrulaması — production'da true olmalı.
    # SPA'ya gizli API key gömülemez; kullanıcı kimliği Firebase Auth ile doğrulanır.
    security_require_auth: bool = False
    firebase_project_id: str = ""
    rate_limit_ask: int = 20
    rate_limit_default: int = 60
    cors_allowed_origins: str = "https://unisense.vercel.app,http://localhost:5173,http://localhost:5174"
    audit_log_path: str = "./logs/audit.log"

    # === Dış kaynaklar ===
    yok_atlas_base: str = "https://yokatlas.yok.gov.tr"
    osym_base: str = "https://www.osym.gov.tr"
    urap_base: str = "https://www.urapcenter.org"

    @field_validator("gemini_api_keys")
    @classmethod
    def _validate_keys(cls, v: str) -> str:
        if not v.strip():
            return v
        keys = [k.strip() for k in v.split(",") if k.strip()]
        for k in keys:
            if not k.startswith("AIza"):
                # Key içeriğini hata mesajına yazma — loglara sızmasın
                raise ValueError("Invalid Gemini key format (must start with 'AIza')")
        return v

    @property
    def gemini_keys_list(self) -> list[str]:
        if self.gemini_api_keys:
            return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]
        if self.gemini_api_key:
            return [self.gemini_api_key]
        return []

    @property
    def api_keys_set(self) -> set[str]:
        return {k.strip() for k in self.security_api_keys.split(",") if k.strip()}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
