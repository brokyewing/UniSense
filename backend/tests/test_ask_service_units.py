"""AskService saf fonksiyon testleri — intent çıkarımı ve cache key."""
from unisense.application.services.ask_service import (
    _estimate_nets,
    _extract_intent,
    _make_cache_key,
)
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
        import pytest

        from unisense.infrastructure.embeddings_local import _model_path

        if not _model_path().exists():
            pytest.skip("static_model.npz yok (HF dataset'ten indirilir)")

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


class TestKpssService:
    def test_kadro_ara_bolum_filtresi(self):
        from unisense.application.services.kpss_service import KpssService

        r = KpssService().kadro_ara(bolum="bilgisayar mühendisliği", duzey="lisans")
        assert r["total"] > 5
        assert any(i["eslesme"].startswith("bölüme özel") for i in r["items"])
        # Kod-bazlı KESİN eşleşme de olmalı (ÖSYM mezuniyet alan kodları)
        assert any(i["eslesme"] == "bölüme özel ✓" for i in r["items"])
        # geçmiş taban eşleşmesi en az bazı kadrolarda olmalı
        assert any(i["gecmis_taban"] for i in r["items"])

    def test_kadro_ara_ascii(self):
        from unisense.application.services.kpss_service import KpssService

        r = KpssService().kadro_ara(bolum="hemsirelik", duzey="lisans")
        assert r["total"] >= 1


class TestSinavRouting:
    def test_kpss_regex(self):
        from unisense.application.services.ask_service import _DGS_RE, _KPSS_RE

        assert _KPSS_RE.search("kpss 85 puanla nereye atanırım")
        assert _KPSS_RE.search("memur olmak istiyorum")
        # YKS bağlamındaki "akademik kadro" KPSS'ye GİTMEMELİ
        assert not _KPSS_RE.search("hacettepe tıp akademik kadrosu nasıl")
        assert _DGS_RE.search("dgs 280 puanla hangi bölümlere geçerim")
        assert _DGS_RE.search("dikey geçiş yapmak istiyorum")

    def test_dgs_service(self):
        from unisense.application.services.dgs_service import DgsService

        r = DgsService().program_ara(puan_turu="SAY", puan=300, bolum="bilgisayar")
        assert r["total"] > 10
        # Taban puanı 300'ün üstünde olan gelmemeli
        assert all((i["min_puan"] or 0) <= 300 for i in r["items"])

    def test_kpss_context_builds(self):
        from unisense.application.services.ask_service import _build_kpss_context

        ctx = _build_kpss_context("kpss 90 puanla bilgisayar mühendisi nereye atanır")
        # Başlık dönem içerir ama "AKTİF/tarih" HARDCODE ETMEZ (BULGU #15)
        assert "KADRO" in ctx and "kadro" in ctx.lower()
        assert "AKTİF TERCİH" not in ctx
        # Bölüm chat'te artık filtreleniyor (BULGU #13) — "tümü" değil
        assert "bölüm=bilgisayar mühendis" in ctx

    def test_kpss_context_toplam_kontenjan(self):
        """İstatistik sorusu → toplam kontenjan özeti; 'kişilik' bölüm sanılmaz."""
        from unisense.application.services.ask_service import _build_kpss_context

        ctx = _build_kpss_context("2026/1 kpss de kaç kişilik açıldı")
        # Dönem geneli özet (tekil örnek değil bütün) verilmeli
        assert "DÖNEM GENELİ" in ctx and "kişilik kontenjan" in ctx
        # "kaç kişilik" → "kişilik" YANLIŞLIKLA bölüm sanılmamalı
        assert "bölüm=kisilik" not in ctx
        assert "bölüm=tümü" in ctx

    def test_exam_track_generic_routing(self):
        """Sınav adı yazılmadan 'puanımla nereye yerleşirim' → profil yolu."""
        from unisense.application.services.ask_service import (
            _DGS_RE,
            _GENERIC_PLACEMENT_RE,
            _KPSS_RE,
        )

        q = "puanımla nereye yerleşebilirim"
        assert _GENERIC_PLACEMENT_RE.search(q)
        assert not _KPSS_RE.search(q) and not _DGS_RE.search(q)


class TestCountAndTercihIntents:
    """Sohbet testinde yakalanan üç gerçek kaçak — sayım/N-tercih/nereleri
    soruları RAG'e düşüp 'elimde yok' cevabı üretiyordu (yapısal veri gerekir)."""

    def test_sayim_sorusu_intent_tetikler(self):
        intent = _extract_intent("toplam kaç tane bilgisayar mühendisliği program kodu var elinde")
        assert intent is not None
        assert intent["is_count"] is True
        assert any("bilgisayar" in d for d in intent["departments"])

    def test_n_tercih_yap_intent_tetikler(self):
        intent = _extract_intent("bana 24 tane tercih yap hepsi bilgisayar mühendisliği olsun")
        assert intent is not None
        assert intent["list_n"] == 24

    def test_tercih_listesi_olustur_sayisiz(self):
        intent = _extract_intent("bilgisayar mühendisliği için tercih listesi oluştur")
        assert intent is not None
        assert intent["list_n"] is None  # sayı yok ama liste isteği tetikledi

    def test_nereleri_tercih_etmeliyim(self):
        intent = _extract_intent("yks puanıma göre bilgisayar mühendisliği istiyorum nereleri tercih etmeliyim")
        assert intent is not None  # 'nereleri' where-kalıbı

    def test_duz_bilgi_sorusu_hala_rag(self):
        # Tetikleyicisiz bölüm sorusu RAG'de kalmalı (aşırı-tetikleme olmasın)
        assert _extract_intent("bilgisayar mühendisliği nedir") is None

    def test_gecersiz_n_sinirlari(self):
        # 0 veya 30 üstü N list_n olmaz ama liste isteği yine tetikler
        intent = _extract_intent("bana 99 tane tercih yap bilgisayar mühendisliği")
        assert intent is not None and intent["list_n"] is None

    def test_dis_muhendislik_icinde_eslesmez(self):
        # "diş" anahtar kelimesi "mühendisliği" substring'inde tetiklenmemeli
        intent = _extract_intent("toplam kaç tane bilgisayar mühendisliği programı var")
        assert intent is not None
        assert not any(d == "diş" for d in intent["departments"])

    def test_dis_hekimligi_hala_eslesir(self):
        intent = _extract_intent("kaç tane diş hekimliği programı var")
        assert intent is not None
        assert any("diş" in d for d in intent["departments"])


class TestNetEstimate:
    def test_net_intent_with_department_routes_to_listing(self):
        # "kaç net" + bölüm → yapısal listeye gitmeli (RAG'e düşmemeli)
        intent = _extract_intent("bilgisayar mühendisliği için kaç net yapmalıyım")
        assert intent is not None
        assert intent["is_net"] is True
        assert any("bilgisayar" in d for d in intent["departments"])

    def test_generic_net_without_department_falls_through(self):
        # Bölüm yoksa özel cevap üretilemez → None (RAG)
        assert _extract_intent("kaç net yapmalıyım") is None

    def test_internet_is_not_net_intent(self):
        # 'internet' yanlış tetiklememeli
        i = _extract_intent("koç üniversitesinde internet var mı")
        assert i is None or i.get("is_net") is False

    def test_estimate_nets_monotonic_and_bounded(self):
        yuksek = _estimate_nets(534.0, "SAY")   # ODTÜ civarı
        dusuk = _estimate_nets(312.0, "SAY")    # ulaşılabilir
        assert yuksek["tyt"] > dusuk["tyt"]
        assert yuksek["ayt"] > dusuk["ayt"]
        assert 0 <= dusuk["tyt"] <= 120 and 0 <= yuksek["ayt"] <= 80

    def test_estimate_nets_tyt_only_type(self):
        e = _estimate_nets(300.0, "TYT")
        assert e["ayt"] is None and 0 <= e["tyt"] <= 120

    def test_estimate_nets_none_score(self):
        assert _estimate_nets(None, "SAY") is None


class TestObpPersonalization:
    def test_parse_obp_direct(self):
        from unisense.application.services.ask_service import _parse_obp_katki
        assert _parse_obp_katki("obp 450") == 54.0          # 450×0.12
        assert _parse_obp_katki("obp'm 420") == 50.4        # ekli hal

    def test_parse_diploma_note(self):
        from unisense.application.services.ask_service import _parse_obp_katki
        assert _parse_obp_katki("diploma notum 90") == 54.0  # 90×5×0.12
        assert _parse_obp_katki("ortalamam 85") == 51.0

    def test_no_obp_returns_none(self):
        from unisense.application.services.ask_service import _parse_obp_katki
        assert _parse_obp_katki("kaç net gerek") is None

    def test_intent_carries_obp_when_net(self):
        i = _extract_intent("diploma notum 90 bilgisayar mühendisliği için kaç net")
        assert i is not None and i["is_net"] and i["obp_katki"] == 54.0

    def test_higher_obp_needs_fewer_nets(self):
        # Aynı taban, yüksek OBP → daha az net gerekir
        az_diploma = _estimate_nets(534.0, "SAY", 30.0)   # düşük OBP
        cok_diploma = _estimate_nets(534.0, "SAY", 60.0)  # yüksek OBP
        assert cok_diploma["tyt"] <= az_diploma["tyt"]
        assert cok_diploma["ayt"] <= az_diploma["ayt"]

    def test_default_used_when_obp_none(self):
        # obp_katki=None → varsayılan (~50) ile aynı sonuç
        from unisense.application.services.ask_service import _OBP_KATKI
        assert _estimate_nets(500.0, "SAY", None) == _estimate_nets(500.0, "SAY", _OBP_KATKI)


class TestTahminiSira:
    def test_higher_score_lower_rank(self):
        from unisense.application.services.recommendation_service import tahmini_sira
        yuksek = tahmini_sira(500.0, "SAY")
        dusuk = tahmini_sira(400.0, "SAY")
        assert yuksek and dusuk
        assert yuksek["tahmini_sira"] < dusuk["tahmini_sira"]  # yüksek puan = iyi sıra
        assert yuksek["tahmini_sira"] >= 1

    def test_all_yks_types_supported(self):
        from unisense.application.services.recommendation_service import tahmini_sira
        for tur in ["SAY", "EA", "SÖZ", "TYT", "DİL"]:
            r = tahmini_sira(420.0, tur)
            assert r is not None and r["tahmini_sira"] >= 1, tur

    def test_unknown_type_returns_none(self):
        from unisense.application.services.recommendation_service import tahmini_sira
        assert tahmini_sira(450.0, "YOK") is None

    def test_none_score_returns_none(self):
        from unisense.application.services.recommendation_service import tahmini_sira
        assert tahmini_sira(None, "SAY") is None

    def test_out_of_range_flags_sinir(self):
        from unisense.application.services.recommendation_service import tahmini_sira
        r = tahmini_sira(600.0, "SAY")  # veri üstü uç
        assert r is not None and r["sinir"] == "ust"
