"""İl → bölge eşlemesi (Kariyer bölge filtresinin temeli).

Kaynaklar il adını farklı yazıyor: ilan.gov.tr "İSTANBUL", yabancı API'ler
(Jooble/Careerjet) "Istanbul". Düz .upper() bunları eşleştiremiyordu (I ≠ İ)
ve bölge sessizce "Bilinmiyor" kalıyordu — filtre boş görünüyordu.
"""
from __future__ import annotations

import pytest

from unisense.domain.geo import PLAKA_KODLARI, REGIONS, il_to_bolge


def test_81_ilin_hepsinin_bolgesi_var():
    eksik = [il for il in PLAKA_KODLARI.values() if il_to_bolge(il) == "Bilinmiyor"]
    assert eksik == [], f"bölgesi bulunamayan iller: {eksik}"


@pytest.mark.parametrize(
    ("yazim", "beklenen"),
    [
        ("İSTANBUL", "Marmara"),
        ("Istanbul", "Marmara"),      # ASCII I — yabancı API yazımı
        ("istanbul", "Marmara"),
        (" İstanbul ", "Marmara"),    # baştaki/sondaki boşluk
        ("ankara", "İç Anadolu"),
        ("ŞANLIURFA", "Güneydoğu Anadolu"),
        ("Sanliurfa", "Güneydoğu Anadolu"),  # aksansız
        ("ÇANAKKALE", "Marmara"),
        ("Canakkale", "Marmara"),
        ("AFYONKARAHİSAR", "Ege"),
        ("Afyonkarahisar", "Ege"),
    ],
)
def test_yazim_farklarina_dayanikli(yazim, beklenen):
    assert il_to_bolge(yazim) == beklenen


@pytest.mark.parametrize("gecersiz", [None, "", "   ", "yokboyle", "12345"])
def test_bilinmeyen_girdi_bilinmiyor_doner(gecersiz):
    assert il_to_bolge(gecersiz) == "Bilinmiyor"


def test_yedi_cografi_bolge_mevcut():
    yedi = {
        "Marmara", "Ege", "Akdeniz", "İç Anadolu",
        "Karadeniz", "Doğu Anadolu", "Güneydoğu Anadolu",
    }
    assert yedi <= set(REGIONS), f"eksik bölge: {yedi - set(REGIONS)}"


class TestIlIlceAyikla:
    """Serbest konum metninden (il, ilce, bolge) çıkarımı.

    İş ilanı kaynakları konumu tek alanda ve TUTARSIZ SIRADA veriyor:
    Jooble "Ankara, Çankaya" (il, ilçe) — Careerjet "Konak, İzmir" (ilçe, il).
    Ölçüm (2026-09-05, 486 kayıt): birleşik alan doğrudan il_to_bolge'ye
    verildiğinde yalnız 147 kayıt çözülüyordu; bu ayıklayıcıyla 460.
    """

    @pytest.mark.parametrize(
        ("konum", "beklenen"),
        [
            ("Ankara, Çankaya", ("Ankara", "Çankaya", "İç Anadolu")),
            ("Konak, İzmir", ("İzmir", "Konak", "Ege")),          # ters sıra
            ("Şişli / İstanbul", ("İstanbul", "Şişli", "Marmara")),  # eğik çizgi
            ("İstanbul", ("İstanbul", None, "Marmara")),          # yalnız il
            ("İstanbul Avrupa", ("İstanbul", "Avrupa", "Marmara")),  # yaka etiketi
            ("İstanbul Anadolu Yakası", ("İstanbul", "Anadolu Yakası", "Marmara")),
        ],
    )
    def test_cozulen_konumlar(self, konum, beklenen):
        from unisense.domain.geo import il_ilce_ayikla

        assert il_ilce_ayikla(konum) == beklenen

    @pytest.mark.parametrize(
        "konum",
        [None, "", "Türkiye", "Remote", "Tuzla, İçmeler"],  # il geçmiyor
    )
    def test_il_yoksa_bilinmiyor(self, konum):
        from unisense.domain.geo import il_ilce_ayikla

        assert il_ilce_ayikla(konum) == (None, None, "Bilinmiyor")

    def test_ilce_alanina_il_adi_tekrarlanmaz(self):
        from unisense.domain.geo import il_ilce_ayikla

        _, ilce, _ = il_ilce_ayikla("İstanbul Avrupa")
        assert ilce == "Avrupa", "ilçe alanına tüm metin yazılmamalı"


class TestIlToBolgeBirlesikMetin:
    """il_to_bolge birleşik konum metnine de dayanıklı olmalı.

    Çağıranlar (ör. kariyer_scraper.v2_kayit) konumu çoğu zaman tek parça
    veriyor: "Ankara, Çankaya". Doğrudan eşleşme tutmayınca bölge sessizce
    "Bilinmiyor" kalıyordu — 486 kayıttan 339'u. Artık ayıklayıcıya düşüyor.
    """

    @pytest.mark.parametrize(
        ("konum", "beklenen"),
        [
            ("Ankara, Çankaya", "İç Anadolu"),
            ("Konak, İzmir", "Ege"),
            ("İstanbul Avrupa", "Marmara"),
            ("Şişli / İstanbul", "Marmara"),
            ("İSTANBUL", "Marmara"),   # doğrudan eşleşme yolu bozulmamalı
            ("Istanbul", "Marmara"),
        ],
    )
    def test_birlesik_metinden_bolge(self, konum, beklenen):
        assert il_to_bolge(konum) == beklenen

    def test_ozyineleme_yok(self):
        """il_to_bolge -> il_ilce_ayikla -> ... sonsuz döngüye girmemeli."""
        import sys

        eski = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        try:
            assert il_to_bolge("Ankara, Çankaya") == "İç Anadolu"
            assert il_to_bolge("bulunamaz bir yer") == "Bilinmiyor"
        finally:
            sys.setrecursionlimit(eski)
