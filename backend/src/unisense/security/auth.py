"""API key authentication."""
from __future__ import annotations

import secrets

from fastapi import Header, Request
from fastapi.security import APIKeyHeader

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import AuthenticationError

logger = get_logger(__name__)

API_KEY_HEADER = "X-API-Key"
api_key_scheme = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def require_api_key(
    request: Request,
    api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
) -> str | None:
    settings = get_settings()
    if not settings.security_require_api_key:
        return None

    valid_keys = settings.api_keys_set
    if not valid_keys:
        logger.error("auth_misconfigured")
        raise AuthenticationError("Sunucu yapılandırma hatası")

    if not api_key:
        raise AuthenticationError("API key gerekli", details={"header": API_KEY_HEADER})

    is_valid = any(secrets.compare_digest(api_key, k) for k in valid_keys)
    if not is_valid:
        client_ip = request.client.host if request.client else "?"
        logger.warning("auth_failed", ip=client_ip, key_prefix=api_key[:8])
        raise AuthenticationError("Geçersiz API key")
    return api_key
