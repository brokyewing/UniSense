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


def _real_client_ip(request: Request) -> str:
    """Sahtecilik-dirençli istemci IP'si (rate-limit anahtarı için).

    GÜVENLİK: uvicorn `--forwarded-allow-ips "*"` ile request.client.host'u
    X-Forwarded-For zincirinin EN SOLuna yazar — ama o değer İSTEMCİ
    KONTROLÜNDEDİR: saldırgan kendi XFF başlığını gönderip her istekte farklı
    bir IP uydurarak IP-bazlı rate-limit kovasını sınırsızca tazeleyebilir
    (limitçiyi tümden atlatır → pahalı uçlarla instance'ı çökertir).

    Render TEK güvenilir proxy olduğundan gerçek istemci IP'si zincirin EN
    SAĞıdır: Render, kendi gördüğü soket IP'sini XFF'in sonuna EKLER. Saldırgan
    sola kaç sahte IP koyarsa koysun en sağı değiştiremez → tek saldırgan = tek
    kova = limit çalışır. (Zincir yoksa uvicorn'un çözdüğü adrese düşülür.)
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        rightmost = xff.split(",")[-1].strip()
        if rightmost:
            return rightmost
    return get_remote_address(request)


def _client_key(request: Request) -> str:
    """Rate limit anahtarı: doğrulanmış kullanıcı varsa uid, yoksa gerçek IP.

    require_user dependency'si uid'i request.state'e yazar; dependency'ler
    endpoint gövdesinden (dolayısıyla limiter sarmalayıcısından) önce çalışır.
    """
    uid = getattr(request.state, "uid", None)
    if uid:
        return f"uid:{uid}"
    return _real_client_ip(request)


def _global_key(*_args) -> str:
    """Site geneli tek kova — /ask günlük GLOBAL tavan için sabit anahtar.

    Her istek aynı anahtara düşer → tüm site toplamı tek limite tabi olur.
    Çok-hesap (açık Firebase kaydı) LLM kota tüketme saldırısına sert backstop.

    DİKKAT: slowapi bu per-limit key_func'u bazı kod yollarında ARGÜMANSIZ,
    bazılarında request ile çağırıyor → *_args ile her iki biçimi de karşıla
    (yoksa /ask her istekte TypeError ile 500 verir — bkz. regresyon testi).
    """
    return "ask:global"


limiter = Limiter(key_func=_client_key)

# Route dekoratörlerinde kullanılacak limit string'leri
ASK_LIMIT = f"{_settings.rate_limit_ask}/minute"
DEFAULT_LIMIT = f"{_settings.rate_limit_default}/minute"
# /ask günlük tavanlar — LLM kota tükenme saldırısına karşı (bkz. config)
ASK_DAILY_LIMIT = f"{_settings.rate_limit_ask_daily}/day"            # hesap/IP başına
ASK_DAILY_GLOBAL_LIMIT = f"{_settings.rate_limit_ask_daily_global}/day"  # site toplamı


def install(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


def ask_limit() -> str:
    return ASK_LIMIT
