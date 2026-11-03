"""Tarih ayrıştırma ve budama kuralları — iki ölçülmüş hatanın regresyon testi.

1. Careerjet RFC-822 tarih veriyor ("Wed, 29 Jun 2026 …"); `[:10]` uygulamak
   "Wed, 29 Ju" üretiyordu — 228 kaydın TAMAMI bozuktu.
2. Budama, yayın tarihi 30 günden eski olan ilanları başvurusu HÂLÂ AÇIK olsa
   bile siliyordu: Savunma Kariyer 24→12, Kariyer Kapısı 33→30 (14 açık ilan).
"""
from __future__ import annotations

import datetime

import pytest

from unisense.infrastructure.scrapers.kariyer_scraper import _merge, _tarih_iso

BUGUN = "2026-09-05"


class TestTarihIso:
    @pytest.mark.parametrize(
        ("ham", "beklenen"),
        [
            ("Wed, 29 Jun 2026 10:00:00 GMT", "2026-06-29"),   # Careerjet
            ("Thu, 03 Sep 2026 08:15:00 +0300", "2026-09-03"),  # offsetli
            ("2026-09-01T10:00:00Z", "2026-09-01"),             # ISO (Jooble)
            ("2026-08-15", "2026-08-15"),                       # düz ISO
        ],
    )
    def test_bicimler_iso_olur(self, ham, beklenen):
        assert _tarih_iso(ham, BUGUN) == beklenen

    @pytest.mark.parametrize("ham", [None, "", "   ", "bozuk tarih"])
    def test_cozulemeyen_bugune_duser(self, ham):
        assert _tarih_iso(ham, BUGUN) == BUGUN

    def test_rfc822_kirpilmaz(self):
        """Eski hata: [:10] -> 'Wed, 29 Ju'."""
        assert _tarih_iso("Wed, 29 Jun 2026 10:00:00 GMT", BUGUN) != "Wed, 29 Ju"


def _kayit(no, tarih, son_basvuru=None):
    k = {
        "id": f"t:{no}", "kaynak": "T", "baslik": f"ilan {no}",
        "tarih": tarih, "url": f"http://x/{no}", "ilk_gorulme": tarih,
    }
    if son_basvuru:
        k["son_basvuru"] = son_basvuru
    return k


class TestBudama:
    """son_basvuru VARSA tek ölçüt odur; yoksa yaş kuralı işler."""

    def test_kurallar(self):
        b = datetime.date.today()
        eski = (b - datetime.timedelta(days=90)).isoformat()
        gelecek = (b + datetime.timedelta(days=35)).isoformat()
        dolmus = (b - datetime.timedelta(days=20)).isoformat()
        yeni_dolmus = (b - datetime.timedelta(days=3)).isoformat()  # 7 gün tolerans

        kayitlar = [
            _kayit(1, eski, gelecek),        # açık ama eski yayın -> KALIR
            _kayit(2, eski, dolmus),         # süresi dolmuş       -> budanır
            _kayit(3, eski),                 # son_basvuru yok, eski -> budanır
            _kayit(4, b.isoformat()),        # son_basvuru yok, yeni -> KALIR
            _kayit(5, eski, yeni_dolmus),    # 3 gün önce doldu (tolerans) -> KALIR
        ]
        kalan = {k["id"] for k in _merge(kayitlar, [])}
        assert kalan == {"t:1", "t:4", "t:5"}

    def test_acik_ilan_yayin_eski_diye_silinmez(self):
        """Asıl hata buydu: kurumsal genel başvuru havuzları eleniyordu."""
        b = datetime.date.today()
        kayit = _kayit(
            9,
            (b - datetime.timedelta(days=200)).isoformat(),
            (b + datetime.timedelta(days=180)).isoformat(),
        )
        assert [k["id"] for k in _merge([kayit], [])] == ["t:9"]


class TestCalismaSekli:
    """Ölçüm 2026-09-06: 1935 kayıttan yalnız 27'sinde çalışma şekli vardı (%1,4).

    Doğrudan beyan ("uzaktan", "hibrit") ilanlarda neredeyse hiç geçmiyor; bu
    yüzden dolaylı sinyal (mağaza/fabrika/şantiye) ve kamu varsayımı devrede.
    İkisi de `detay.calisma_sekli_kaynak` ile işaretleniyor — arayüz bunları
    beyan gibi göstermemeli. Kapsam 27 -> 568 (%29,4).
    """

    def _v2(self, **alan):
        from unisense.infrastructure.scrapers.kariyer_scraper import v2_kayit
        temel = {"id": "x:1", "kaynak": "T", "baslik": "", "ozet": "",
                 "url": "http://x/1", "tarih": BUGUN}
        return v2_kayit({**temel, **alan})

    @pytest.mark.parametrize(
        ("baslik", "beklenen", "kaynak"),
        [
            ("Uzaktan Yazılım Geliştirici", "online", "beyan"),
            ("Backend Developer (Home Office)", "online", "beyan"),
            ("Hibrit çalışma - Veri Analisti", "hibrit", "beyan"),
            ("Ofiste çalışma / Muhasebe", "yuzyuze", "beyan"),
            ("Mağaza Satış Danışmanı", "yuzyuze", "dolayli"),
            ("Fabrika Üretim Operatörü", "yuzyuze", "dolayli"),
            ("Yazılım Uzmanı", "bilinmiyor", "-"),
        ],
    )
    def test_metinden_cikarim(self, baslik, beklenen, kaynak):
        k = self._v2(baslik=baslik)
        assert k["calisma_sekli"] == beklenen
        if kaynak != "-":
            assert k["detay"]["calisma_sekli_kaynak"] == kaynak

    def test_kamu_varsayimi_isaretlenir(self):
        """Kamu kadrosu yerinde varsayılır ama 'varsayim' diye damgalanır."""
        k = self._v2(baslik="Sözleşmeli Personel Alımı", hat="kamu")
        assert k["calisma_sekli"] == "yuzyuze"
        assert k["detay"]["calisma_sekli_kaynak"] == "varsayim"

    def test_ozel_hatta_varsayim_yok(self):
        assert self._v2(baslik="Uzman", hat="ozel")["calisma_sekli"] == "bilinmiyor"

    def test_kaynak_degeri_ezilmez(self):
        """Lever `workplaceType` gibi kaynak alanı çıkarımdan üstündür."""
        k = self._v2(baslik="Mağaza Müdürü", calisma_sekli="online")
        assert k["calisma_sekli"] == "online"
        assert k["detay"]["calisma_sekli_kaynak"] == "kaynak"
