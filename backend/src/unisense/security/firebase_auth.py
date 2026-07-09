"""Firebase ID token authentication.

Frontend, Firebase Auth ile giriş yapan kullanıcının ID token'ını
`Authorization: Bearer <token>` header'ında gönderir. Burada token
Google'ın public sertifikalarıyla doğrulanır — service account
credential'ı GEREKMEZ, sadece FIREBASE_PROJECT_ID yeterlidir.

SECURITY_REQUIRE_AUTH=false iken (local dev) doğrulama atlanır.
"""
from __future__ import annotations

import threading

from fastapi import Header, Request

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import AuthenticationError

logger = get_logger(__name__)

_lock = threading.Lock()
_firebase_app = None
_init_failed = False


def _get_firebase_app():
    """firebase_admin app'ini lazy + thread-safe başlat."""
    global _firebase_app, _init_failed
    if _firebase_app is not None or _init_failed:
        return _firebase_app
    with _lock:
        if _firebase_app is not None or _init_failed:
            return _firebase_app
        try:
            import firebase_admin

            settings = get_settings()
            options = {}
            if settings.firebase_project_id:
                options["projectId"] = settings.firebase_project_id
            try:
                _firebase_app = firebase_admin.get_app()
            except ValueError:
                _firebase_app = firebase_admin.initialize_app(options=options or None)
        except Exception as e:  # noqa: BLE001
            _init_failed = True
            logger.error("firebase_init_failed", error=str(e)[:200])
    return _firebase_app


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

    app = _get_firebase_app()
    if app is None:
        logger.error("auth_misconfigured", reason="firebase_admin init failed")
        raise AuthenticationError("Sunucu yapılandırma hatası")

    from firebase_admin import auth as fb_auth

    try:
        decoded = fb_auth.verify_id_token(token, app=app)
    except Exception as e:  # noqa: BLE001 — expired/revoked/invalid hepsi 401
        client_ip = request.client.host if request.client else "?"
        logger.warning("auth_token_invalid", ip=client_ip, error=str(e)[:120])
        raise AuthenticationError("Geçersiz veya süresi dolmuş oturum") from None

    uid: str | None = decoded.get("uid")
    request.state.uid = uid
    return uid
