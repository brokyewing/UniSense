"""Kariyer servisi + scraper saf fonksiyon testleri (dosya/ağ yok)."""
from datetime import date

from unisense.application.services.kariyer_service import (
    _KAYNAKLAR,
    filtrele,
)
from unisense.infrastructure.scrapers.kariyer_scraper import (
    _bolum_etiketle,
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
        assert [x["id"] for x in filtrele(ks, hat="kamu", bugun=BUGUN)[0]] == ["a"]

    def test_q_turkce_duyarsiz(self):
        ks = [_k("a", baslik="Sözleşmeli Bilişim Personeli Alımı")]
        assert len(filtrele(ks, q="sozlesmeli bilisim", bugun=BUGUN)[0]) == 1
        assert filtrele(ks, q="hemşire", bugun=BUGUN)[0] == []

    def test_sehir(self):
        ks = [_k("a", sehir="İstanbul"), _k("b", sehir="Ankara")]
        assert [x["id"] for x in filtrele(ks, sehir="ankara", bugun=BUGUN)[0]] == ["b"]

    def test_yeni_bayragi_ve_filtre(self):
        ks = [_k("yeni", ilk="2026-09-04"), _k("eski", ilk="2026-08-20")]
        hepsi = {x["id"]: x["yeni"] for x in filtrele(ks, bugun=BUGUN)[0]}
        assert hepsi == {"yeni": True, "eski": False}
        assert [x["id"] for x in filtrele(ks, sadece_yeni=True, bugun=BUGUN)[0]] == ["yeni"]

    def test_limit_ve_sira(self):
        ks = [_k(f"k{i}", tarih=f"2026-09-0{i}") for i in range(1, 6)]
        out, toplam = filtrele(ks, limit=2, bugun=BUGUN)
        assert [x["id"] for x in out] == ["k5", "k4"]  # en güncel önce
        assert toplam == 5


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


class TestBolum:
    def test_cift_tarafli_coklu_etiket(self):
        from unisense.core.text import fold_tr
        tags = _bolum_etiketle(fold_tr(
            "Bilgisayar mühendisi aranıyor; yazılım geliştirme ve siber güvenlik bilgisi"))
        assert {"bilgisayar", "yazilim", "siber"} <= set(tags)

    def test_eslesmeyen_bos(self):
        from unisense.core.text import fold_tr
        assert _bolum_etiketle(fold_tr("Garson aranıyor, deneyimli")) == []

    def test_normalize_etiket_tasiyor(self):
        k = _jooble_normalize(
            {"id": 9, "title": "Elektrik Bakım Mühendisi", "link": "https://x.jobs/9",
             "snippet": "PLC ve otomasyon bilen"}, "2026-09-05")
        assert {"elektrik_elektronik", "mekatronik"} <= set(k["bolumler"])

    def test_filtre_bolum(self):
        a = _k("a", ilk="2026-09-05")
        a["bolumler"] = ["bilgisayar", "yazilim"]
        b = _k("b", ilk="2026-09-05")
        b["bolumler"] = ["insaat"]
        assert [x["id"] for x in filtrele([a, b], bolum="yazilim", bugun=BUGUN)[0]] == ["a"]


class TestFiltrelerF11:
    def _r(self, id_, **kw):
        d = _k(id_, ilk="2026-09-05")
        d.update(kw)
        return d

    def test_il_alt_dize(self):
        a = self._r("a", il="İstanbul", sehir="")
        b = self._r("b", il="", sehir="Ankara, Türkiye")
        assert [x["id"] for x in filtrele([a, b], il="ankara", bugun=BUGUN)[0]] == ["b"]

    def test_bolge_birebir(self):
        a = self._r("a", bolge="Marmara")
        b = self._r("b", bolge="Ege")
        assert [x["id"] for x in filtrele([a, b], bolge="marmara", bugun=BUGUN)[0]] == ["a"]

    def test_calisma_istihdam_deneyim(self):
        a = self._r("a", calisma_sekli="online", istihdam_turu="tam_zamanli",
                    deneyim="yeni_mezun")
        b = self._r("b", calisma_sekli="yuzyuze", istihdam_turu="staj",
                    deneyim="2_5")
        r = filtrele([a, b], calisma_sekli="online", istihdam_turu="tam_zamanli",
                      deneyim="yeni_mezun", bugun=BUGUN)[0]
        assert [x["id"] for x in r] == ["a"]

    def test_coklu_secim(self):
        a = self._r("a", calisma_sekli="online")
        b = self._r("b", calisma_sekli="hibrit")
        c = self._r("c", calisma_sekli="yuzyuze")
        r = filtrele([a, b, c], calisma_sekli=["online", "hibrit"], bugun=BUGUN)[0]
        assert {x["id"] for x in r} == {"a", "b"}

    def test_kpss_uc_durum(self):
        a = self._r("a", kpss=True)
        b = self._r("b", kpss=False)
        c = self._r("c", kpss=None)
        assert [x["id"] for x in filtrele([a, b, c], kpss=True, bugun=BUGUN)[0]] == ["a"]
        assert [x["id"] for x in filtrele([a, b, c], kpss=False, bugun=BUGUN)[0]] == ["b"]
        assert len(filtrele([a, b, c], bugun=BUGUN)[0]) == 3

    def test_sayfalama(self):
        ks = [self._r(f"k{i}", tarih=f"2026-09-0{i}") for i in range(1, 6)]
        s1, t1 = filtrele(ks, sayfa=1, boyut=2, bugun=BUGUN)
        s2, t2 = filtrele(ks, sayfa=2, boyut=2, bugun=BUGUN)
        assert [x["id"] for x in s1] == ["k5", "k4"]
        assert [x["id"] for x in s2] == ["k3", "k2"]
        assert t1 == t2 == 5

    def test_legacy_limit_calismaya_devam(self):
        ks = [self._r(f"k{i}") for i in range(5)]
        out, toplam = filtrele(ks, limit=3, bugun=BUGUN)
        assert len(out) == 3 and toplam == 5

    def test_siralama_son_basvuru(self):
        a = self._r("a", tarih="2026-09-05", son_basvuru="2026-09-20")
        b = self._r("b", tarih="2026-09-05", son_basvuru="2026-09-08")
        c = self._r("c", tarih="2026-09-05", son_basvuru=None)
        out, _ = filtrele([a, b, c], sira="son_basvuru_asc", bugun=BUGUN)
        assert [x["id"] for x in out] == ["b", "a", "c"]

    def test_merge_30gun_budama(self):
        taze = _k("taze", tarih="2026-09-05", ilk="2026-09-05")
        bayat = _k("bayat", tarih="2026-07-01", ilk="2026-07-01")
        tarihsiz = {"id": "x", "tarih": "", "ilk_gorulme": ""}
        out = _merge([taze, bayat, tarihsiz], [])
        assert {x["id"] for x in out} == {"taze", "x"}

    def test_merge_union_eski_korunur(self):
        # Artımlı taramada çekilmeyen eski kayıt silinmez
        eski = [_k("eski", tarih="2026-09-01", ilk="2026-09-01")]
        out = _merge([_k("yeni", tarih="2026-09-05", ilk="2026-09-05")], eski)
        assert {x["id"] for x in out} == {"yeni", "eski"}

    def test_merge_suresi_dolmus_duser(self):
        eski = [{**_k("vadesi_gecmis", tarih="2026-08-20", ilk="2026-08-20"),
                 "son_basvuru": "2026-08-25"}]
        out = _merge([], eski)
        assert out == []


class TestSemaV2:
    def test_eski_id_cevrilir(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _v2_id
        assert _v2_id({"id": "jooble-123", "kaynak": "Jooble"}) == "jooble:123"
        assert _v2_id({"id": "cj-abc", "kaynak": "Careerjet"}) == "careerjet:abc"
        assert _v2_id({"id": "rg-2026-09-05", "kaynak": "Resmî Gazete"}) == "rg:2026-09-05"
        assert _v2_id({"id": "jooble:123", "kaynak": "Jooble"}) == "jooble:123"

    def test_kayipsiz_tasima(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import v2_kayit
        k = v2_kayit({**_k("a", tarih="2026-09-05", ilk="2026-09-01"),
                      "sehir": "İstanbul", "ozet": "x" * 500})
        for alan in ("id", "kaynak_kod", "il", "ilce", "bolge", "calisma_sekli",
                     "istihdam_turu", "deneyim", "pozisyon_etiket", "kpss",
                     "maas", "son_basvuru"):
            assert alan in k, alan
        assert k["il"] == "İstanbul" and k["bolge"] == "Marmara"
        assert k["calisma_sekli"] == "bilinmiyor" and k["kpss"] is None
        assert len(k["ozet"]) == 300
        assert k["ilk_gorulme"] == "2026-09-01"  # korunur

    def test_merge_eski_yeni_id_esisir(self):
        eski = [{**_k("a", ilk="2026-09-01"), "id": "jooble-123",
                 "kaynak": "Jooble"}]
        yeni = [{**_k("a", ilk="2026-09-05"), "id": "jooble:123",
                 "kaynak": "Jooble"}]
        out = _merge(yeni, eski)
        assert len(out) == 1 and out[0]["ilk_gorulme"] == "2026-09-01"


class TestCalismaSekli:
    def test_online(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _calisma_sekli
        from unisense.core.text import fold_tr
        assert _calisma_sekli(fold_tr("Uzaktan çalışma, remote ekip")) == "online"
        assert _calisma_sekli(fold_tr("Home office imkânı")) == "online"

    def test_hibrit_oncelikli(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _calisma_sekli
        from unisense.core.text import fold_tr
        # Açık "hibrit" anahtarı + remote sinyali → hibrit kazanır
        assert _calisma_sekli(fold_tr("Hibrit çalışma, remote günler mevcut")) == "hibrit"

    def test_yuzyuze(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _calisma_sekli
        from unisense.core.text import fold_tr
        assert _calisma_sekli(fold_tr("Yerinde çalışma, ofis ortamında")) == "yuzyuze"

    def test_bilinmiyor(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _calisma_sekli
        from unisense.core.text import fold_tr
        assert _calisma_sekli(fold_tr("Mühendis aranıyor")) == "bilinmiyor"

    def test_geriye_donuk_cikarim(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import v2_kayit
        k = v2_kayit({**_k("a"), "baslik": "Uzaktan yazılım geliştirici",
                      "ozet": "", "calisma_sekli": "bilinmiyor"})
        assert k["calisma_sekli"] == "online"


class TestKamuilan:
    ORNEK_LI = ("<li><time class='cbp_tmtime'><h4>4</h4><h3> Eylül</h3></time>"
                "<div class='cbp_tmlabel'><a href='ilanDetay.aspx?kod=ABC123' class='xx'>"
                "<div><p class='alt_p1'>KARADENİZ TEKNİK ÜNİVERSİTESİ</p>"
                "<p class='alt_p2'> 93 SÖZLEŞMELİ PERSONEL ALACAK"
                "<em>( 4 Eylül - 18 Eylül) </em></p></div></a></div>")

    def test_tr_tarih(self):
        from datetime import date
        from unisense.infrastructure.scrapers.kariyer_scraper import _tr_tarih
        assert _tr_tarih("4", "Eylül", date(2026, 9, 5)) == "2026-09-04"
        assert _tr_tarih("18", "Eylül", date(2026, 9, 5)) == "2026-09-18"
        assert _tr_tarih("x", "Eylül", date(2026, 9, 5)) == ""

    def test_timeline_parse(self):
        import re
        li = self.ORNEK_LI
        a = re.search(r"<a\s+href='(ilanDetay\.aspx\?kod=[^']+)'", li)
        kurum = re.search(r"<p class='alt_p1'>(.*?)</p>", li, re.S)
        baslik = re.search(r"<p class='alt_p2'>(.*?)<em", li, re.S)
        assert a and kurum and baslik
        assert "KARADENİZ" in kurum.group(1)
        assert "SÖZLEŞMELİ" in baslik.group(1)


class TestHatB:
    def test_jooble_normalize(self):
        k = _jooble_normalize(
            {"id": 123, "title": "Yazılım Geliştirici", "link": "https://x.jobs/1",
             "source": "kariyer.net", "location": "İstanbul",
             "snippet": "<b>Java</b> aranıyor", "salary": "100bin", "type": "Tam zamanlı"},
            "2026-09-05")
        assert k["id"] == "jooble:123"
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
        assert k["id"].startswith("careerjet:") and k["kurum"] == "Acme"
        assert k["tarih"] == "2026-09-04"

    def test_anahtar_yoksa_atlama(self, monkeypatch):
        import requests

        monkeypatch.delenv("JOOBLE_API_KEY", raising=False)
        monkeypatch.delenv("CAREERJET_API_KEY", raising=False)
        assert _scrape_hatb(requests.Session()) == []


class TestDefter:
    def test_varsayilan_defter_yuklenir(self):
        from unisense.infrastructure.scrapers.kariyer_registry import yukle
        girdiler = yukle()
        kodlar = {g["kod"] for g in girdiler if g.get("aktif")}
        assert {"rg", "jooble", "careerjet", "kamuilan", "kariyerkapisi",
                "akademiktr"} <= kodlar

    def test_davranis_paritesi(self):
        # Defter değerleri eski gömülü sabitlerle aynı olmalı
        from unisense.infrastructure.scrapers import kariyer_scraper as ks
        from unisense.infrastructure.scrapers.kariyer_registry import yukle
        d = {g["kod"]: g for g in yukle()}
        assert [(s["keywords"], s.get("location", "")) for s in d["jooble"]["sorgular"]] == list(ks._HATB_JOOBLE_SORGULAR)
        assert list(d["careerjet"]["sorgular"]) == list(ks._HATB_CJ_SORGULAR)
        assert d["jooble"]["sayfa"] == ks._HATB_SAYFA_JOOBLE
        assert d["careerjet"]["sayfa"] == ks._HATB_SAYFA_CJ
        assert d["rg"]["params"]["max_pdf_mb"] == 64

    def test_bozuk_defter_reddedilir(self, tmp_path):
        from unisense.infrastructure.scrapers.kariyer_registry import yukle
        import pytest
        p = tmp_path / "defter.yml"
        p.write_text("kaynaklar:\n  - {kod: x, ad: X}\n", encoding="utf-8")
        with pytest.raises(ValueError):
            yukle(p)
        p.write_text("kaynaklar:\n  - {kod: x, ad: X, hat: kamu, url: u, erisim: ufo}\n",
                     encoding="utf-8")
        with pytest.raises(ValueError):
            yukle(p)


class TestKosuRaporu:
    def test_kaynak_bazinda_sayim(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _kosu_raporu
        yeni = [
            {"id": "jooble:1", "kaynak": "Jooble"},
            {"id": "jooble:2", "kaynak": "Jooble"},
            {"id": "kamuilan:9", "kaynak": "kamuilan.sbb.gov.tr"},
        ]
        r = _kosu_raporu(yeni, {"jooble:1"}, {"rg": "SSLError"}, "2026-09-05")
        assert r["tarih"] == "2026-09-05"
        assert r["kaynaklar"]["jooble"] == {"cekilen": 2, "yeni": 1, "hata": ""}
        assert r["kaynaklar"]["kamuilan"] == {"cekilen": 1, "yeni": 1, "hata": ""}
        assert r["kaynaklar"]["rg"]["hata"].startswith("SSLError")

    def test_olu_kaynak_alarmi(self, tmp_path):
        import json
        from unisense.infrastructure.scrapers.kariyer_scraper import _gecmis_guncelle
        p = tmp_path / "kosu.json"

        def kos(gun, cekilen):
            # main() akışı: geçmiş oku → güncelle → yaz
            g, a = _gecmis_guncelle(p, gun, cekilen)
            p.write_text(json.dumps({"gecmis": g}), encoding="utf-8")
            return g, a

        _, a1 = kos("2026-09-03", {"jooble": 0, "rg": 1})
        assert a1 == []  # geçmiş yetersiz
        _, a2 = kos("2026-09-04", {"jooble": 0, "rg": 1})
        assert a2 == []
        g3, a3 = kos("2026-09-05", {"jooble": 0, "rg": 1})
        assert a3 == ["jooble"]  # üst üste 3×0
        # Aynı gün tekrar koşu üzerine yazar, şişirmez; alarm kalkar
        g4, a4 = kos("2026-09-05", {"jooble": 3, "rg": 1})
        assert len(g4) == 3 and g4[-1]["cekilen"]["jooble"] == 3
        assert a4 == []


class TestCaprazDedup:
    def _r(self, id_, hat, baslik, kurum, il, ilk="2026-09-05", bolumler=None):
        return {"id": id_, "hat": hat, "baslik": baslik, "kurum": kurum,
                "il": il, "ilk_gorulme": ilk, "bolumler": bolumler or []}

    def test_kamu_kazanir(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _dedup_capraz
        ozel = self._r("jooble:1", "ozel", "Bilgisayar Mühendisi", "X Kurumu",
                       "Ankara", ilk="2026-09-01", bolumler=["bilgisayar"])
        kamu = self._r("kamuilan:9", "kamu", "bilgisayar MÜHENDİSİ ", "x kurumu ",
                       "ankara", ilk="2026-09-05", bolumler=["yazilim"])
        out, n = _dedup_capraz([ozel, kamu])
        assert n == 1 and len(out) == 1
        assert out[0]["hat"] == "kamu"  # kamu kazandı
        assert out[0]["ilk_gorulme"] == "2026-09-01"  # eski tarih korundu
        assert set(out[0]["bolumler"]) == {"bilgisayar", "yazilim"}  # etiket birleşti

    def test_bos_baslik_kurum_birlesmez(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _dedup_capraz
        a = self._r("a", "ozel", "", "X", "Ankara")
        b = self._r("b", "ozel", "", "X", "Ankara")
        out, n = _dedup_capraz([a, b])
        assert n == 0 and len(out) == 2

    def test_farkli_il_birlesmez(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _dedup_capraz
        a = self._r("a", "ozel", "Mühendis", "X", "Ankara")
        b = self._r("b", "ozel", "Mühendis", "X", "İzmir")
        out, n = _dedup_capraz([a, b])
        assert n == 0 and len(out) == 2


class TestKariyerKapisi:
    ORNEK_RSS = """<?xml version="1.0" encoding="utf-8"?><rss><channel>
    <item><guid isPermaLink="true">https://kariyerkapisi.gov.tr/IlanDetay?i=abc-123</guid>
    <link>https://kariyerkapisi.gov.tr/IlanDetay?i=abc-123</link>
    <category>Sözleşmeli Personel İlanları</category>
    <title>ANKARA ÜNİVERSİTESİ - Sözleşmeli Bilişim Personeli Alım İlanı</title>
    <description>x</description>
    <pubDate>Thu, 04 Sep 2026 00:00:00 +0300</pubDate></item>
    <item><title>Eksik kayıt</title></item>
    </channel></rss>"""

    def test_rss_parse(self):
        import xml.etree.ElementTree as ET
        from email.utils import parsedate_to_datetime
        kok = ET.fromstring(self.ORNEK_RSS)
        items = list(kok.iter("item"))
        assert len(items) == 2
        baslik = items[0].find("title").text
        kurum, _, _ = baslik.partition(" - ")
        assert kurum == "ANKARA ÜNİVERSİTESİ"
        assert parsedate_to_datetime(items[0].find("pubDate").text).date().isoformat() == "2026-09-04"

    def test_istihdam_esleme(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _kk_istihdam
        assert _kk_istihdam("Sözleşmeli Personel İlanları") == "sozlesmeli"
        assert _kk_istihdam("A Grubu Memur (Kariyer Meslek)") == "bilinmiyor"


class TestAkademiktr:
    LISTE = ('<a href="/ilan/ege-universitesi-ogretim-elemani-alim-ilani-1">x</a>'
             '<a href="/ilan/ege-universitesi-ogretim-elemani-alim-ilani-1">x</a>'
             '<a href="/ilan/istanbul">yön</a>')
    DETAY = ('<h1 class="detail-title-new">Ege Üniversitesi Öğretim Elemanı Alım İlanı</h1>'
             '<span>01.09.2026</span><span>16.09.2026</span>')

    def test_liste_parse(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _akademiktr_parse_liste
        out = _akademiktr_parse_liste(self.LISTE)
        assert out == ["/ilan/ege-universitesi-ogretim-elemani-alim-ilani-1"]

    def test_detay_parse(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _akademiktr_parse_detay
        p = _akademiktr_parse_detay(self.DETAY)
        assert p["baslik"].startswith("Ege Üniversitesi")
        assert p["tarihler"] == ["2026-09-01", "2026-09-16"]


class TestIlangovtr:
    ORNEK_AD = {
        "id": 2211464, "title": "Kurum X 2 Mühendis Alacak", "adNo": "ILN02540001",
        "advertiserName": "Kurum X", "addressCityName": "Ankara",
        "addressCountyName": "Çankaya", "publishStartDate": "2026-09-03T21:00:00Z",
        "urlStr": "/ilan/2211464/kamu-personel-alimi-test",
        "adTypeFilters": [{"key": "İlan Türü", "value": "PERSONEL ALIMI"}],
    }

    def test_personel_filtresi(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _ilangovtr_personel_mi
        assert _ilangovtr_personel_mi(self.ORNEK_AD) is True
        assert _ilangovtr_personel_mi({"adTypeFilters": [{"key": "İlan Türü", "value": "İHALE"}]}) is False
        assert _ilangovtr_personel_mi({}) is False

    def test_normalize(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _ilangovtr_normalize
        k = _ilangovtr_normalize(self.ORNEK_AD, "2026-09-05")
        assert k["id"] == "ilangovtr:2211464"
        assert k["hat"] == "kamu" and k["il"] == "ANKARA" and k["ilce"] == "Çankaya"
        assert k["bolge"] == "İç Anadolu" and k["tarih"] == "2026-09-03"
        assert k["url"].startswith("https://www.ilan.gov.tr/ilan/2211464")
        assert k["bolumler"] == []  # çıplak "mühendis" bölüm eşlemez (nitelikli kalıp gerekir)

    def test_defter_girdisi(self):
        from unisense.infrastructure.scrapers.kariyer_registry import yukle
        d = {g["kod"]: g for g in yukle()}
        assert d["ilangovtr"]["erisim"] == "api" and d["ilangovtr"]["aktif"] is True

    def test_erken_durus(self):
        # 2 sayfa üst üste yenilik yoksa durur (günlük artımlı tarama)
        from unisense.infrastructure.scrapers import kariyer_scraper as ks

        def sahte_ad(i):
            return {"id": i, "title": "Personel Alınacak", "advertiserName": "K",
                    "addressCityName": "Ankara", "addressCountyName": "",
                    "publishStartDate": "2026-09-05T00:00:00Z", "urlStr": f"/ilan/{i}/x",
                    "adTypeFilters": [{"key": "İlan Türü", "value": "PERSONEL ALIMI"}]}

        sayfalar = [[sahte_ad(1), sahte_ad(2)], [sahte_ad(1)], []]

        class SahteOturum:
            def __init__(self):
                self.n = 0

            def post(self, *a, **k):
                sayfa = sayfalar[min(self.n, len(sayfalar) - 1)]
                self.n += 1

                class R:
                    def raise_for_status(self):
                        pass

                    def json(self):
                        return {"result": {"ads": sayfa}}
                return R()

        out = ks._scrape_ilangovtr(SahteOturum(), {"ilangovtr:1", "ilangovtr:2"})
        assert {k["id"] for k in out} == {"ilangovtr:1", "ilangovtr:2"}


class TestSavunmakariyer:
    def test_kayit_uretim_activity_elenir(self):
        from unisense.infrastructure.scrapers import kariyer_scraper as ks

        sayfalar = [
            {"content": [
                {"id": "a1", "jobTitle": "Yazılım Mühendisi", "companyName": "X",
                 "jobLocation": "Ankara", "jobType": "FULL_TIME",
                 "jobDescription": "<p>Java</p>", "startDate": "2026-09-01T00:00:00",
                 "endDate": "2026-09-20T00:00:00"},
                {"id": "a2", "jobTitle": "Bootcamp", "companyName": "Y",
                 "jobType": "ACTIVITY"},
            ], "totalPages": 2},
            {"content": [], "totalPages": 2},
        ]

        class SahteOturum:
            def __init__(self):
                self.n = 0

            def post(self, *a, **k):
                i = min(self.n, 1)
                self.n += 1

                class R:
                    def raise_for_status(self):
                        pass

                    def json(sr):
                        return {"data": sayfalar[i]}
                return R()

        out = ks._scrape_savunmakariyer(SahteOturum())
        assert [k["id"] for k in out] == ["savunmakariyer:a1"]
        assert out[0]["istihdam_turu"] == "tam_zamanli"
        assert out[0]["son_basvuru"] == "2026-09-20"
        assert out[0]["kpss"] is False


class TestTurksat:
    BOS = ('<table class="G GE"><tr><td><table class="no-record">'
           '<tr><td>Yayınlanmış bir açık pozisyon bulunamadı.</td></tr>'
           '</table></td></tr></table>')
    DOLU = ('<table class="G GE"><tr><td><a href="/jobs/123">Yazılım Mühendisi</a>'
            ' - Ankara, son başvuru 20.09.2026</td></tr></table>')

    def test_bos_durum(self):
        from unisense.infrastructure.scrapers import kariyer_scraper as ks

        class SahteOturum:
            def get(self, *a, **k):
                class R:
                    text = TestTurksat.BOS
                return R()

        assert ks._scrape_turksat(SahteOturum()) == []

    def test_dolu_satir_parse(self):
        import re
        m = re.search(r'href="(/jobs?/[^"]+|/job[^"]+|/ilan[^"]+)"', self.DOLU)
        assert m and m.group(1) == "/jobs/123"

    def test_varsayilan_defter_turksat(self):
        from unisense.infrastructure.scrapers.kariyer_registry import yukle
        d = {g["kod"]: g for g in yukle()}
        assert d["turksat"]["erisim"] == "html"


class TestKpssCikarim:
    def test_kpss_var_ve_tur(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _kpss_bilgi
        from unisense.core.text import fold_tr
        var_mi, tur = _kpss_bilgi(fold_tr("KPSS P3 puanıyla mühendis alımı"))
        assert var_mi is True and tur == "P3"
        var_mi, tur = _kpss_bilgi(fold_tr("P93 puan türünden en az 70"))
        assert var_mi is True and tur == "P93"

    def test_kpss_yoksa_none(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import _kpss_bilgi
        from unisense.core.text import fold_tr
        assert _kpss_bilgi(fold_tr("Yazılım geliştirici aranıyor")) == (None, None)

    def test_geriye_donuk_v2(self):
        from unisense.infrastructure.scrapers.kariyer_scraper import v2_kayit
        k = v2_kayit({**_k("a"), "baslik": "KPSS P3 ile memur alımı",
                      "ozet": "", "kpss": None})
        assert k["kpss"] is True
        assert k["detay"]["kpss_tur"] == "P3"


class TestSirketAts:
    def test_esleme_yuklenir(self):
        from unisense.infrastructure.scrapers.kariyer_registry import sirket_ats
        liste = sirket_ats()
        assert len(liste) >= 8
        aktif = [e for e in liste if e.get("durum") == "aktif"]
        assert {e["pano"] for e in aktif} >= {"spyke-games", "getmidas",
                                             "biggergames", "codeway"}
        lever = [e for e in liste if e.get("ats") == "lever"]
        assert all(e.get("pano") for e in lever)

