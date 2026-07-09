"""Rate limit anahtar fonksiyonu testleri."""
from types import SimpleNamespace

from unisense.api.middleware.rate_limit import ASK_LIMIT, DEFAULT_LIMIT, _client_key


def test_limits_are_per_minute_strings():
    assert ASK_LIMIT.endswith("/minute")
    assert DEFAULT_LIMIT.endswith("/minute")


def test_key_prefers_authenticated_uid():
    request = SimpleNamespace(
        state=SimpleNamespace(uid="user123"),
        client=SimpleNamespace(host="1.2.3.4"),
    )
    assert _client_key(request) == "uid:user123"


def test_key_falls_back_to_ip():
    request = SimpleNamespace(
        state=SimpleNamespace(),
        client=SimpleNamespace(host="1.2.3.4"),
    )
    assert _client_key(request) == "1.2.3.4"
