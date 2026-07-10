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


class TestListingIntent:
    """Şehir/üniversite + bölüm envanter soruları — sıra/puan olmadan tetiklenir."""

    def test_city_plus_department_triggers(self):
        intent = _extract_intent("istanbul ünilerinde tıp kaç puan kaç kişi var")
        assert intent is not None
        assert "İSTANBUL" in intent["cities"]
        assert "tıp" in intent["departments"]

    def test_city_suffix_matches(self):
        # "ankara'daki", "ankaradaki" gibi ek almış haller
        intent = _extract_intent("ankaradaki hukuk fakülteleri hangileri")
        assert intent is not None
        assert "ANKARA" in intent["cities"]

    def test_department_without_location_no_trigger(self):
        # Sadece bölüm adı → saf RAG (listeleme tetiklenmez)
        assert _extract_intent("tıp okumak zor mu") is None

    def test_where_query_triggers_listing(self):
        # "nerede/hangi üniversitede/var mı" + bölüm → şehirsiz listeleme
        for q in ["gastronomi bölümü hangi üniversitelerde var",
                  "pastacılık bölümü var mı",
                  "odyoloji nerede okunur"]:
            intent = _extract_intent(q)
            assert intent is not None, q
            assert intent["departments"], q

    def test_city_suffix_traps(self):
        # "bölüm"→BOLU, "karşı"→KARS tuzakları tetiklenmemeli
        intent = _extract_intent("gastronomi bölümü nasıl bir bölüm")
        assert intent is None  # tanıtım sorusu → RAG'e gitmeli
        i2 = _extract_intent("tıp bölümüne karşı ilgim var mı bilmiyorum")
        assert i2 is None or "KARS" not in i2.get("cities", [])
        # Gerçek şehir ekleri çalışmaya devam etmeli
        i3 = _extract_intent("boluda tıp var mı")
        assert i3 is not None and "BOLU" in i3["cities"]

    def test_university_detection(self):
        from unisense.application.services.recommendation_service import detect_universities

        assert detect_universities("hacettepede tıp taban puanı") != []
        assert detect_universities("koç üniversitesi tıp kontenjanı") != []
        # Şehir adı tek başına üniversiteye bağlanmamalı
        assert detect_universities("istanbul gezilecek yerler") == []

    def test_ascii_typing_tolerance(self):
        """Mobil klavye ASCII yazımı ("cerrahpasa tip") da çalışmalı."""
        from unisense.application.services.recommendation_service import detect_universities

        assert detect_universities("cerrahpasa tip siralamasi") != []
        assert detect_universities("bogazici bilgisayar") != []

        intent = _extract_intent("istanbul tip fakulteleri kac puan")
        assert intent is not None
        assert "İSTANBUL" in intent["cities"]
        assert "tıp" in intent["departments"]

    def test_embed_fold_fallback(self):
        """ASCII sorgu, Türkçe karakterli sorguyla neredeyse aynı vektörü vermeli."""
        import numpy as np

        from unisense.infrastructure.embeddings import embed_query

        v1 = embed_query("tıp fakültesi sıralaması")
        v2 = embed_query("tip fakultesi siralamasi")
        # Homograf temizliği yapılmış modelde ~1.0; eski modelde de yüksek olmalı
        assert float(np.dot(v1, v2)) > 0.85

    def test_listing_returns_programs(self):
        from unisense.core.di import get_recommendation_service

        result = get_recommendation_service().list_programs(
            cities=["İSTANBUL"], dept_keywords=["tıp"], limit=10
        )
        assert result["total"] > 20  # İstanbul'da onlarca tıp programı var
        assert result["total_quota"] > 1000
        assert len(result["programs"]) == 10
        # En iyi sıra başta
        ranks = [p["base_rank"] for p in result["programs"] if p["base_rank"]]
        assert ranks == sorted(ranks)


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
