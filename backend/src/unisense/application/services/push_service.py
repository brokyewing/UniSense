"""Push notification service — FCM ile bildirim gönderimi.

Firebase Admin SDK kullanarak FCM mesajları gönderir.
Service account key (GOOGLE_APPLICATION_CREDENTIALS) gerekli.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Firebase Admin SDK — opsiyonel, yoksa graceful fail
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    _FIREBASE_ADMIN_AVAILABLE = False
    logger.warning("firebase_admin not installed — push notifications disabled")


def _init_firebase_admin():
    """Firebase Admin SDK'yı başlat (idempotent)."""
    if not _FIREBASE_ADMIN_AVAILABLE:
        return False
    try:
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        logger.error("firebase_admin init failed: %s", e)
        return False


def send_push_notification(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    icon: str = "/logo.png",
    click_action: str = "/",
) -> dict[str, Any]:
    """FCM ile push bildirim gönder.

    Args:
        tokens: FCM token listesi
        title: Bildirim başlığı
        body: Bildirim metni
        data: Ek veri (deep link vb.)
        icon: Bildirim ikonu
        click_action: Tıklanınca açılacak URL

    Returns:
        {"success": int, "failure": int, "errors": list}
    """
    if not _FIREBASE_ADMIN_AVAILABLE:
        return {"success": 0, "failure": len(tokens), "errors": ["firebase_admin not available"]}

    if not _init_firebase_admin():
        return {"success": 0, "failure": len(tokens), "errors": ["firebase_admin init failed"]}

    if not tokens:
        return {"success": 0, "failure": 0, "errors": []}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        tokens=tokens,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                icon=icon,
                badge="/logo.png",
                click_action=click_action,
            ),
            fcm_options=messaging.WebpushFCMOptions(link=click_action),
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
        errors = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                errors.append(f"token[{idx}]: {resp.exception}")
        return {
            "success": response.success_count,
            "failure": response.failure_count,
            "errors": errors,
        }
    except Exception as e:
        logger.error("push send failed: %s", e)
        return {"success": 0, "failure": len(tokens), "errors": [str(e)]}


def get_user_fcm_tokens(uid: str) -> list[str]:
    """Kullanıcının FCM token'larını Firestore'dan oku.

    Frontend, enablePush() ile token'ları users/{uid}/pushTokens/{token} altına yazar.
    """
    # Bu fonksiyon Firestore'dan token'ları okur
    # Backend'de Firestore Admin SDK gerekli — şimdilik boş döner
    # TODO: firebase-admin ile Firestore'dan token'ları oku
    return []


def send_exam_reminder(uid: str, exam_name: str, days_left: int):
    """Sınav hatırlatma bildirimi gönder."""
    tokens = get_user_fcm_tokens(uid)
    if not tokens:
        return
    title = f"📅 {exam_name} yaklaşıyor!"
    body = f"Sınava {days_left} gün kaldı. Çalışmaya devam et! 💪"
    send_push_notification(tokens, title, body, data={"type": "exam_reminder", "exam": exam_name})


def send_streak_reminder(uid: str, streak: int):
    """Seri hatırlatma bildirimi gönder."""
    tokens = get_user_fcm_tokens(uid)
    if not tokens:
        return
    title = "🔥 Serini koru!"
    body = f"{streak} günlük serin var. Bugün de çalışmayı unutma!"
    send_push_notification(tokens, title, body, data={"type": "streak_reminder"})