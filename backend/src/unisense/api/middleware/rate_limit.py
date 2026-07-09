"""Rate limiting.

Not: Limitler route'lara `@limiter.limit(...)` dekoratörüyle uygulanır —
sadece install() çağırmak yetmez. Proxy (Render/Cloudflare) arkasında
gerçek istemci IP'si için uvicorn `--proxy-headers` ile çalışmalı.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from unisense.core.config import get_settings

_settings = get_settings()


def _client_key(request: Request) -> str:
    """Rate limit anahtarı: doğrulanmış kullanıcı varsa uid, yoksa IP.

    require_user dependency'si uid'i request.state'e yazar; dependency'ler
    endpoint gövdesinden (dolayısıyla limiter sarmalayıcısından) önce çalışır.
    """
    uid = getattr(request.state, "uid", None)
    if uid:
        return f"uid:{uid}"
    return get_remote_address(request)


limiter = Limiter(key_func=_client_key)

# Route dekoratörlerinde kullanılacak limit string'leri
ASK_LIMIT = f"{_settings.rate_limit_ask}/minute"
DEFAULT_LIMIT = f"{_settings.rate_limit_default}/minute"


def install(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


def ask_limit() -> str:
    return ASK_LIMIT
