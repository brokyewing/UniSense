"""Firebase ID token doğrulaması — service account GEREKTİRMEZ.

Frontend, Firebase Auth ile giriş yapan kullanıcının ID token'ını
`Authorization: Bearer <token>` header'ında gönderir. Token, Google'ın
halka açık sertifikalarıyla doğrulanır (imza + süre + audience + issuer).

NOT: firebase-admin KULLANILMIYOR — onun verify_id_token'ı Application
Default Credentials (service account dosyası) istiyor; Render free'de
gereksiz kurulum yükü. google-auth'un JWT doğrulaması aynı işi
credential'sız yapar (Firebase'in 3. parti doğrulama dokümanındaki yöntem).

SECURITY_REQUIRE_AUTH=false iken (local dev) doğrulama atlanır.
"""
from __future__ import annotations

import time

from fastapi import Header, Request

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import AuthenticationError

logger = get_logger(__name__)

# Firebase ID token'larını imzalayan sertifikalar (halka açık endpoint)
_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)
_CERTS_TTL_S = 3600

_certs_cache: dict | None = None
_certs_fetched_at: float = 0.0


def _get_certs() -> dict:
    """Google imza sertifikalarını getir (1 saat cache'li)."""
    global _certs_cache, _certs_fetched_at
    now = time.time()
    if _certs_cache is None or now - _certs_fetched_at > _CERTS_TTL_S:
        import requests

        resp = requests.get(_CERTS_URL, timeout=10)
        resp.raise_for_status()
        _certs_cache = resp.json()
        _certs_fetched_at = now
        logger.info("firebase_certs_refreshed", keys=len(_certs_cache))
    return _certs_cache


def _verify_token(token: str, project_id: str) -> dict:
    """Firebase ID token'ı doğrula, claim'leri döndür. Hatalıysa raise eder."""
    from google.auth import jwt as google_jwt

    claims = google_jwt.decode(token, certs=_get_certs(), audience=project_id)
    # google_jwt.decode imza + exp + aud kontrol eder; issuer'ı biz doğrularız
    expected_iss = f"https://securetoken.google.com/{project_id}"
    if claims.get("iss") != expected_iss:
        raise ValueError(f"Beklenmeyen issuer: {claims.get('iss')}")
    if not claims.get("sub"):
        raise ValueError("Token'da kullanıcı (sub) yok")
    return claims


def require_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str | None:
    """Doğrulanmış Firebase kullanıcısının uid'ini döner.

    - SECURITY_REQUIRE_AUTH=false → None (doğrulama yok, local dev)
    - Token geçersiz/eksik → 401
    - uid ayrıca request.state.uid'e yazılır (rate limit key'i için)
    """
    settings = get_settings()
    if not settings.security_require_auth:
        return None

    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError(
            "Bu özellik için giriş yapmalısın",
            details={"header": "Authorization"},
        )
    token = authorization[len("Bearer "):].strip()

    if not settings.firebase_project_id:
        logger.error("auth_misconfigured", reason="FIREBASE_PROJECT_ID tanımsız")
        raise AuthenticationError("Sunucu yapılandırma hatası")

    try:
        claims = _verify_token(token, settings.firebase_project_id)
    except Exception as e:  # noqa: BLE001 — expired/invalid/imza hepsi 401
        client_ip = request.client.host if request.client else "?"
        logger.warning("auth_token_invalid", ip=client_ip, error=str(e)[:120])
        raise AuthenticationError("Geçersiz veya süresi dolmuş oturum") from None

    uid: str = claims["sub"]
    request.state.uid = uid
    return uid
