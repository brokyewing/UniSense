"""Rate limit anahtar fonksiyonu testleri."""
from types import SimpleNamespace

from unisense.api.middleware.rate_limit import (
    ASK_LIMIT,
    DEFAULT_LIMIT,
    _client_key,
    _real_client_ip,
)


def _req(uid=None, host="1.2.3.4", xff=None):
    """Sahte Request: state.uid, client.host ve x-forwarded-for başlığı."""
    headers = {}
    if xff is not None:
        headers["x-forwarded-for"] = xff
    return SimpleNamespace(
        state=SimpleNamespace(uid=uid) if uid else SimpleNamespace(),
        client=SimpleNamespace(host=host),
        headers=headers,
    )


def test_limits_are_per_minute_strings():
    assert ASK_LIMIT.endswith("/minute")
    assert DEFAULT_LIMIT.endswith("/minute")


def test_key_prefers_authenticated_uid():
    # XFF olsa bile giriş yapmış kullanıcı uid'e keylenir
    assert _client_key(_req(uid="user123", xff="9.9.9.9")) == "uid:user123"


def test_key_falls_back_to_ip_without_xff():
    assert _client_key(_req(host="1.2.3.4")) == "1.2.3.4"


def test_real_ip_uses_rightmost_xff_hop():
    # Render gerçek istemci IP'sini zincirin SONUNA ekler → en sağ güvenilir
    assert _real_client_ip(_req(xff="1.1.1.1, 2.2.2.2, 9.9.9.9")) == "9.9.9.9"


def test_spoofed_left_xff_cannot_rotate_the_bucket():
    # GÜVENLİK: saldırgan sola farklı sahte IP'ler koysa da anahtar SABİT kalır
    # (en sağdaki gerçek IP değişmez) → limit atlatılamaz
    k1 = _client_key(_req(xff="7.7.7.7, 203.0.113.5"))
    k2 = _client_key(_req(xff="8.8.8.8, 203.0.113.5"))
    k3 = _client_key(_req(xff="1.2.3.4, 5.6.7.8, 203.0.113.5"))
    assert k1 == k2 == k3 == "203.0.113.5"


def test_single_xff_entry_is_used():
    assert _real_client_ip(_req(xff="203.0.113.9")) == "203.0.113.9"
