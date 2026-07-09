"""AskService saf fonksiyon testleri — intent çıkarımı ve cache key."""
from unisense.application.services.ask_service import _extract_intent, _make_cache_key
from unisense.domain.models import ChatTurn, Query


class TestExtractIntent:
    def test_plain_query_returns_none(self):
        assert _extract_intent("Koç Üniversitesi hakkında bilgi ver") is None

    def test_rank_bin_format(self):
        intent = _extract_intent("300 bin sıralamayla bilgisayar mühendisliği okuyabilir miyim")
        assert intent is not None
        assert intent["rank"] == 300_000
        assert any("bilgisayar" in d for d in intent["departments"])

    def test_rank_dotted_format(self):
        intent = _extract_intent("50.000 sıra ile nereye girerim")
        assert intent is not None
        assert intent["rank"] == 50_000

    def test_score_with_type(self):
        intent = _extract_intent("450 puanla eşit ağırlık hangi bölümler")
        assert intent is not None
        assert intent["score"] == 450
        assert intent["score_type"] == "EA"

    def test_uni_type_filter(self):
        intent = _extract_intent("100 bin sıra devlet üniversitesi")
        assert intent is not None
        assert "Devlet" in intent["uni_types"]

    def test_geo_flag_alone_triggers_intent(self):
        intent = _extract_intent("deniz kenarında üniversiteler")
        assert intent is not None
        assert "coastal" in intent["geo_flags"]


class TestCacheKey:
    def _q(self, **kw):
        defaults = dict(text="test sorgusu", top_k=12, history=[], model_preference="gemini")
        defaults.update(kw)
        return Query(**defaults)

    def test_same_input_same_key(self):
        assert _make_cache_key(self._q(), "gemini") == _make_cache_key(self._q(), "gemini")

    def test_different_query_different_key(self):
        assert _make_cache_key(self._q(), "gemini") != _make_cache_key(
            self._q(text="başka sorgu"), "gemini"
        )

    def test_different_top_k_different_key(self):
        # top_k retrieval sonucunu değiştirir — cache key'e dahil olmalı
        assert _make_cache_key(self._q(top_k=5), "gemini") != _make_cache_key(
            self._q(top_k=20), "gemini"
        )

    def test_history_changes_key(self):
        with_history = self._q(history=[ChatTurn(role="user", text="önceki mesaj")])
        assert _make_cache_key(self._q(), "gemini") != _make_cache_key(with_history, "gemini")
