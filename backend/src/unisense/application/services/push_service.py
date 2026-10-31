import json
import os

from unisense.core.logging import get_logger

logger = get_logger(__name__)

# Firebase Admin SDK — opsiyonel bağımlılık
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    _FIREBASE_ADMIN_AVAILABLE = False
    logger.warning("firebase_admin not installed — push notifications disabled")

# Service account key yolu (env veya default)
_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-service-account.json")
_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

_firebase_app = None

def _init_firebase():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    if not _FIREBASE_ADMIN_AVAILABLE:
        return None

    cred = None
    if _SERVICE_ACCOUNT_JSON:
        try:
            cred = credentials.Certificate(json.loads(_SERVICE_ACCOUNT_JSON))
        except Exception as e:
            logger.error("firebase_admin json parse error", error=str(e))
            return None
    elif os.path.exists(_SERVICE_ACCOUNT_PATH):
        try:
            cred = credentials.Certificate(_SERVICE_ACCOUNT_PATH)
        except Exception as e:
            logger.error("firebase_admin cert error", error=str(e))
            return None
    else:
        logger.warning("firebase_admin service account not found", path=_SERVICE_ACCOUNT_PATH)
        return None

    try:
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("firebase_admin initialized")
        return _firebase_app
    except Exception as e:
        logger.error("firebase_admin init error", error=str(e))
        return None


def send_push_notification(tokens: list[str], title: str, body: str, data: dict | None = None) -> dict:
    """FCM push bildirim gönder."""
    app = _init_firebase()
    if app is None:
        return {"status": "disabled", "message": "Firebase Admin SDK not available"}

    if not tokens:
        return {"status": "skipped", "message": "No tokens provided"}

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        logger.info("push_sent", success=response.success_count, failure=response.failure_count)
        return {
            "status": "ok",
            "success": response.success_count,
            "failure": response.failure_count,
        }
    except Exception as e:
        logger.error("push_send_error", error=str(e))
        return {"status": "error", "message": str(e)}


def send_exam_reminder(uid: str, exam_type: str = "YKS", days_left: int = 30) -> dict:
    """Sınav hatırlatma bildirimi gönder."""
    return send_push_notification(
        tokens=[],
        title=f"{exam_type} Sınavı Hatırlatması",
        body=f"{exam_type} sınavına {days_left} gün kaldı. Çalışmaya devam et!",
        data={"type": "exam_reminder", "exam_type": exam_type, "days_left": str(days_left)},
    )


def send_streak_reminder(uid: str, streak: int = 0) -> dict:
    """Seri hatırlatma bildirimi gönder."""
    return send_push_notification(
        tokens=[],
        title="Çalışma Serin 🔥",
        body=f"{streak} günlük serin var. Bugün de çalışarak serini koru!",
        data={"type": "streak_reminder", "streak": str(streak)},
    )