"""FastAPI app entrypoint.

Kullanım:
    uvicorn unisense.main:app --host 0.0.0.0 --port 8002 --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from unisense.api.middleware import error_handler, logging as request_log, rate_limit
from unisense.api.v1.routes import router as v1_router
from unisense.core.config import get_settings
from unisense.core.di import get_vector_store
from unisense.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: embedding modeli + ChromaDB index'i önceden ısıt.

    Cold start sırasında ilk /api/v1/ask çağrısı normalde sentence-transformers
    modelini yüklemek için ~10sn bekletir. Burada startup'ta önceden ısıtarak
    ilk gerçek istek p50'sini ~4sn'ye düşürürüz.
    """
    logger = get_logger(__name__)
    logger.info("lifespan_warmup_start")
    try:
        store = get_vector_store()
        store.warmup()
        logger.info("lifespan_warmup_complete")
    except Exception as e:
        logger.error("lifespan_warmup_error", error=str(e))
    yield
    # Shutdown — DI cache temizliği gerekmez (process bitince düşer)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    app = FastAPI(
        title="UniSense API",
        version="0.1.0",
        description="UniSense — Türkiye üniversite tercih asistanı (RAG + sıralama veritabanı)",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID", "Authorization"],
    )

    rate_limit.install(app)
    request_log.install(app)
    error_handler.install(app)

    app.include_router(v1_router)

    logger.info(
        "app_starting",
        env=settings.app_env,
        port=settings.app_port,
        cors_origins=settings.cors_origins_list,
    )
    return app


app = create_app()


def run() -> None:
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "unisense.main:app",
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.app_log_level.lower(),
        reload=not settings.is_production,
    )


if __name__ == "__main__":
    run()
