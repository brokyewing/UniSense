"""Settings config — Gemini key format validator dayanıklılığı.

Regresyon: eskiden tek bozuk key ValueError fırlatıp tüm Settings()'i (ve
dolayısıyla backend boot'unu + her workflow'u) çökertiyordu. Artık bozuk
key'ler DÜŞÜRÜLÜR, geçerliler kalır.
"""
from unisense.core.config import Settings


def _s(keys: str) -> Settings:
    # _env_file=None: gerçek backend/.env'i okuma → test deterministik kalsın
    return Settings(gemini_api_keys=keys, _env_file=None)


def test_valid_keys_kept():
    s = _s("AIzaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,AQ.AbcDef123456")
    assert len(s.gemini_keys_list) == 2


def test_invalid_key_dropped_not_raised():
    # Eskiden burada ValueError → Settings çökerdi. Artık sessizce düşer.
    s = _s("some-wrong-value-123")
    assert s.gemini_keys_list == []


def test_mixed_keeps_valid_drops_invalid():
    s = _s("AIzaGood1234567890,bad-one,AQ.Good2xyz")
    assert s.gemini_keys_list == ["AIzaGood1234567890", "AQ.Good2xyz"]


def test_empty_stays_empty():
    assert _s("").gemini_keys_list == []
    assert _s("   ").gemini_keys_list == []
