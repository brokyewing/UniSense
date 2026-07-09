"""Kimlik doğrulama testleri — Firebase token dependency davranışı."""
from types import SimpleNamespace

import pytest

from unisense.core.config import get_settings
from unisense.domain.exceptions import AuthenticationError
from unisense.security.firebase_auth import require_user


def _fake_request():
    return SimpleNamespace(client=None, state=SimpleNamespace())


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_auth_disabled_returns_none(monkeypatch):
    monkeypatch.setenv("SECURITY_REQUIRE_AUTH", "false")
    assert require_user(_fake_request(), authorization=None) is None


def test_auth_enabled_missing_header_raises_401(monkeypatch):
    monkeypatch.setenv("SECURITY_REQUIRE_AUTH", "true")
    with pytest.raises(AuthenticationError):
        require_user(_fake_request(), authorization=None)


def test_auth_enabled_wrong_scheme_raises_401(monkeypatch):
    monkeypatch.setenv("SECURITY_REQUIRE_AUTH", "true")
    with pytest.raises(AuthenticationError):
        require_user(_fake_request(), authorization="Basic dXNlcjpwYXNz")
