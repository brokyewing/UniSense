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
            ("Ankara, Çankaya", ("ANKARA", "Çankaya", "İç Anadolu")),
            ("Konak, İzmir", ("İZMİR", "Konak", "Ege")),          # ters sıra
            ("Şişli / İstanbul", ("İSTANBUL", "Şişli", "Marmara")),  # eğik çizgi
            ("İstanbul", ("İSTANBUL", None, "Marmara")),          # yalnız il
            ("İstanbul Avrupa", ("İSTANBUL", "Avrupa", "Marmara")),  # yaka etiketi
            ("İstanbul Anadolu Yakası", ("İSTANBUL", "Anadolu Yakası", "Marmara")),
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


class TestMetindenIlBul:
    """Kurum adından il çıkarımı.

    Kamu kaynaklarının çoğu ayrı şehir alanı vermiyor; il yalnız kurum adında
    geçiyor. Ölçüm (2026-09-05, ili boş 128 kayıt): kelime taraması 64,
    istisna tablosuyla birlikte 82 kayıt çözülüyor.
    """

    @pytest.mark.parametrize(
        ("metin", "beklenen"),
        [
            ("ARDAHAN ÜNİVERSİTESİ REKTÖRLÜĞÜ", "ARDAHAN"),
            ("BURSA TEKNİK ÜNİVERSİTESİ", "BURSA"),
            ("BARTIN ÜNİVERSİTESİ", "BARTIN"),
            # adında il geçmeyenler — istisna tablosu
            ("KARADENİZ TEKNİK ÜNİVERSİTESİ", "TRABZON"),
            ("ORTA DOĞU TEKNİK ÜNİVERSİTESİ REKTÖRLÜĞÜ", "ANKARA"),
            ("GEBZE TEKNİK ÜNİVERSİTESİ", "KOCAELİ"),
            ("İNEBOLU BELEDİYE BAŞKANLIĞI", "KASTAMONU"),
            ("KUZEY ANADOLU KALKINMA AJANSI", "KASTAMONU"),
        ],
    )
    def test_kurumdan_il_cikar(self, metin, beklenen):
        from unisense.domain.geo import metinden_il_bul

        assert metinden_il_bul(metin) == beklenen

    @pytest.mark.parametrize("metin", [None, "", "2026-09-05 Resmî Gazete sayıları"])
    def test_bulunamayan_none_doner(self, metin):
        from unisense.domain.geo import metinden_il_bul

        assert metinden_il_bul(metin) is None

    def test_cikan_il_bolgeye_cozulur(self):
        """Çıkarılan il mutlaka il_to_bolge ile bölgeye çözülebilmeli."""
        from unisense.domain.geo import metinden_il_bul

        for metin in ("KARADENİZ TEKNİK ÜNİVERSİTESİ", "ARDAHAN ÜNİVERSİTESİ"):
            il = metinden_il_bul(metin)
            assert il and il_to_bolge(il) != "Bilinmiyor"


class TestKanonikIl:
    """İl adı tek yazıma indirgenmeli.

    Ölçüm (2026-09-05, 1965 kayıt): `il` alanında 355 farklı değer vardı;
    yalnız İstanbul'un ~95 varyantı ("İstanbul", "İSTANBUL", "İstanbul Avrupa",
    "Ataşehir, İstanbul", "Istanbul"…). Kanonikleştirmeyle 65 ile indi,
    İstanbul tek değerde (955 kayıt) toplandı.
    """

    @pytest.mark.parametrize(
        "yazim", ["İSTANBUL", "istanbul", "Istanbul", "İstanbul", " İstanbul "]
    )
    def test_ayni_kanonik_deger(self, yazim):
        from unisense.domain.geo import kanonik_il

        assert kanonik_il(yazim) == kanonik_il("İstanbul")

    @pytest.mark.parametrize("gecersiz", [None, "", "yokboyle", "Türkiye"])
    def test_taninmayan_none(self, gecersiz):
        from unisense.domain.geo import kanonik_il

        assert kanonik_il(gecersiz) is None

    @pytest.mark.parametrize(
        "konum",
        [
            "İstanbul", "İSTANBUL", "Istanbul", "İstanbul Avrupa",
            "İstanbul Anadolu Yakası", "Ataşehir, İstanbul", "İstanbul, Fatih",
            "Şişli / İstanbul",
        ],
    )
    def test_tum_varyantlar_tek_ile_iner(self, konum):
        """Kullanıcının bildirdiği sorun: aynı şehir birden çok kez görünüyordu."""
        from unisense.domain.geo import il_ilce_ayikla, kanonik_il

        il, _, bolge = il_ilce_ayikla(konum)
        assert il == kanonik_il("İstanbul")
        assert bolge == "Marmara"

    def test_metinden_il_bul_de_kanonik_doner(self):
        from unisense.domain.geo import kanonik_il, metinden_il_bul

        assert metinden_il_bul("BURSA TEKNİK ÜNİVERSİTESİ") == kanonik_il("Bursa")


class TestIlceden:
    """İl yazılmamış konumlar ("Sarıyer, Maslak") ilçe adından çözülür.

    Kaynak: turkey_geo.json `central_districts`. Birden çok ilde geçen ilçe
    adları (Yenişehir, Merkez...) indekse ALINMAZ — yanlış il atamaktansa
    boş bırakmak doğru.
    """

    @pytest.mark.parametrize(
        ("konum", "il", "ilce"),
        [
            ("Sarıyer, Maslak", "İSTANBUL", "Sarıyer"),
            ("Sincan, Yenikent", "ANKARA", "Sincan"),
            ("Bornova, Atatürk", "İZMİR", "Bornova"),
            ("Nilüfer, İhsaniye", "BURSA", "Nilüfer"),
            ("Küçükçekmece, Sefaköy", "İSTANBUL", "Küçükçekmece"),
            ("Ortahisar, Beşirli", "TRABZON", "Ortahisar"),
        ],
    )
    def test_ilceden_il_cozulur(self, konum, il, ilce):
        from unisense.domain.geo import il_ilce_ayikla
        assert il_ilce_ayikla(konum)[:2] == (il, ilce)

    @pytest.mark.parametrize("konum", ["Türkiye", "Yenişehir, Egriçam", ""])
    def test_belirsiz_bos_kalir(self, konum):
        """Tahmin etmektense bilinmiyor demek doğru."""
        from unisense.domain.geo import il_ilce_ayikla
        assert il_ilce_ayikla(konum) == (None, None, "Bilinmiyor")

    def test_il_yaziliysa_ilce_indeksi_devreye_girmez(self):
        from unisense.domain.geo import il_ilce_ayikla
        assert il_ilce_ayikla("Ankara, Çankaya")[:2] == ("ANKARA", "Çankaya")
