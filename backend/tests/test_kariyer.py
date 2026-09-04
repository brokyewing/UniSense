"""Kariyer servisi + scraper saf fonksiyon testleri (dosya/ağ yok)."""
from datetime import date

from unisense.application.services.kariyer_service import (
    _KAYNAKLAR,
    filtrele,
)
from unisense.infrastructure.scrapers.kariyer_scraper import (
    _careerjet_normalize,
    _eslesme_say,
    _gunluk_sayilar,
    _jooble_normalize,
    _merge,
    _scrape_hatb,
)

BUGUN = date(2026, 9, 5)


def _k(id_, hat="kamu", baslik="Test", kurum="", sehir="", tarih="2026-09-05",
       ilk="2026-09-05"):
    return {"id": id_, "hat": hat, "kaynak": "Resmî Gazete", "baslik": baslik,
            "kurum": kurum, "sehir": sehir, "tarih": tarih, "url": "",
            "ozet": "", "detay": {}, "ilk_gorulme": ilk}


class TestFiltrele:
    def test_hat(self):
        ks = [_k("a", hat="kamu"), _k("b", hat="ozel")]
        assert [x["id"] for x in filtrele(ks, hat="kamu", bugun=BUGUN)] == ["a"]

    def test_q_turkce_duyarsiz(self):
        ks = [_k("a", baslik="Sözleşmeli Bilişim Personeli Alımı")]
        assert len(filtrele(ks, q="sozlesmeli bilisim", bugun=BUGUN)) == 1
        assert filtrele(ks, q="hemşire", bugun=BUGUN) == []

    def test_sehir(self):
        ks = [_k("a", sehir="İstanbul"), _k("b", sehir="Ankara")]
        assert [x["id"] for x in filtrele(ks, sehir="ankara", bugun=BUGUN)] == ["b"]

    def test_yeni_bayragi_ve_filtre(self):
        ks = [_k("yeni", ilk="2026-09-04"), _k("eski", ilk="2026-08-20")]
        hepsi = {x["id"]: x["yeni"] for x in filtrele(ks, bugun=BUGUN)}
        assert hepsi == {"yeni": True, "eski": False}
        assert [x["id"] for x in filtrele(ks, sadece_yeni=True, bugun=BUGUN)] == ["yeni"]

    def test_limit_ve_sira(self):
        ks = [_k(f"k{i}", tarih=f"2026-09-0{i}") for i in range(1, 6)]
        out = filtrele(ks, limit=2, bugun=BUGUN)
        assert [x["id"] for x in out] == ["k5", "k4"]  # en güncel önce


class TestScraperSaf:
    def test_gunluk_sayilar(self):
        html = ('<a href="https://www.resmigazete.gov.tr/eskiler/2026/09/20260905.pdf">x</a>'
                '<a href="https://www.resmigazete.gov.tr/eskiler/2026/09/20260905-2.pdf">y</a>'
                '<a href="https://ornek.com/baska.pdf">z</a>')
        s = _gunluk_sayilar(html)
        assert list(s) == ["2026-09-05"]
        assert len(s["2026-09-05"]) == 2

    def test_eslesme(self):
        from unisense.core.text import fold_tr
        m = _eslesme_say(fold_tr("Sözleşmeli bilişim personeli ve KPSS şartı ile mühendis alımı"))
        assert m["sozlesmeli_bilisim"] >= 1
        assert m["kpss"] >= 1
        assert m["siber_guvenlik"] == 0

    def test_merge_ilk_gorulme_korunur(self):
        eski = [_k("rg-2026-09-04", ilk="2026-09-04")]
        yeni = [_k("rg-2026-09-04", ilk="2026-09-05"),
                _k("rg-2026-09-05", ilk="2026-09-05")]
        out = _merge(yeni, eski)
        assert {x["id"]: x["ilk_gorulme"] for x in out} == {
            "rg-2026-09-04": "2026-09-04", "rg-2026-09-05": "2026-09-05"}


class TestRehber:
    def test_iki_hat_var(self):
        hatlar = {k["hat"] for k in _KAYNAKLAR}
        assert {"kamu", "ozel"} <= hatlar

    def test_kariyer_kapisi_ve_vizyoner_var(self):
        ids = {k["id"] for k in _KAYNAKLAR}
        assert {"kariyer-kapisi", "vizyoner-genc", "ilan-gov-tr"} <= ids

    def test_pdf_kapsami_tamamlandi(self):
        ids = {k["id"] for k in _KAYNAKLAR}
        assert {"milli-saraylar", "spor-toto", "ssb", "epdk-rekabet-btk",
                "iletisim", "kamu-bankalari", "csb-yerel", "sozlesmeli-bilisim",
                "kamuis", "isinolsa", "kamuilan-net", "kamuajans"} <= ids

    def test_ek_kaynaklar_2026_09(self):
        ids = {k["id"] for k in _KAYNAKLAR}
        assert {"iskur-acik-is", "elemanonline", "cvyolla", "stajim",
                "jooble"} <= ids


class TestHatB:
    def test_jooble_normalize(self):
        k = _jooble_normalize(
            {"id": 123, "title": "Yazılım Geliştirici", "link": "https://x.jobs/1",
             "source": "kariyer.net", "location": "İstanbul",
             "snippet": "<b>Java</b> aranıyor", "salary": "100bin", "type": "Tam zamanlı"},
            "2026-09-05")
        assert k["id"] == "jooble-123"
        assert k["hat"] == "ozel" and k["kurum"] == "kariyer.net"
        assert k["ozet"] == "Java aranıyor"

    def test_jooble_bos_link_elenir(self):
        assert _jooble_normalize({"title": "X", "link": "ftp://a"}, "2026-09-05") is None

    def test_careerjet_normalize(self):
        k = _careerjet_normalize(
            {"title": "Backend Dev", "url": "https://y.jobs/2", "company": "Acme",
             "locations": "Ankara", "description": "Python <b>bilgisi</b>",
             "date": "2026-09-04", "salary": "", "site": "careerjet.com.tr"},
            "2026-09-05")
        assert k["id"].startswith("cj-") and k["kurum"] == "Acme"
        assert k["tarih"] == "2026-09-04"

    def test_anahtar_yoksa_atlama(self, monkeypatch):
        import requests

        monkeypatch.delenv("JOOBLE_API_KEY", raising=False)
        monkeypatch.delenv("CAREERJET_API_KEY", raising=False)
        assert _scrape_hatb(requests.Session()) == []
