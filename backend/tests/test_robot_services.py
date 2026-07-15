"""LGS/TUS tercih robotu servis birim testleri.

Kova mantığı (güvenli/tutar/riskli eşikleri), il/ilçe/tür/kontenjan filtreleri
ve çok-yıllı trend değerlendirmesi — sahte veriyle, dosya/ağ bağımlılığı yok.
"""
import unisense.application.services.lgs_service as lgs_mod
import unisense.application.services.tus_service as tus_mod
from unisense.application.services.lgs_service import LgsService, _degerlendir
from unisense.application.services.tus_service import TusService


def _lise(okul, il, ilce, tur, yuzdelik, trend=None):
    return {
        "okul": okul, "il": il, "ilce": ilce, "tur": tur, "dil": "İngilizce",
        "taban_puan": 400.0, "yuzdelik": yuzdelik, "kontenjan": 100,
        "pansiyon": None, "trend": trend or [],
    }


FAKE_LGS = {
    "guncelleme": "2026-07", "kaynak": "test", "not": "test", "yil": 2025, "toplam": 4,
    "liseler": [
        # Öğrenci yüzdeliği 2.0 için: t*0.8=3.2'den büyük t → güvenli
        _lise("Kolay Lisesi", "İSTANBUL", "KADIKÖY", "anadolu", 4.0),
        # 2.0 <= 2.2 ve > 2.2*0.8=1.76 → tutar
        _lise("Sınır Lisesi", "İSTANBUL", "KADIKÖY", "fen", 2.2),
        # 1.8 < 2.0 <= 1.8*1.25=2.25 → riskli
        _lise("Zor Lisesi", "İSTANBUL", "BEŞİKTAŞ", "fen", 1.8),
        # 2.0 > 1.0*1.25 → kapsam dışı
        _lise("Çok Zor Lisesi", "ANKARA", "ÇANKAYA", "fen", 1.0),
    ],
}


class TestDegerlendir:
    def test_zorlasiyor(self):
        r = _degerlendir({"trend": [{"yil": 2025, "yuzdelik": 0.4}, {"yil": 2022, "yuzdelik": 0.6}]})
        assert r["trend_yonu"] == "zorlasiyor"

    def test_kolaylasiyor(self):
        r = _degerlendir({"trend": [{"yil": 2025, "yuzdelik": 6.0}, {"yil": 2022, "yuzdelik": 4.0}]})
        assert r["trend_yonu"] == "kolaylasiyor"

    def test_istikrarli(self):
        r = _degerlendir({"trend": [{"yil": 2025, "yuzdelik": 0.44}, {"yil": 2022, "yuzdelik": 0.39}]})
        assert r["trend_yonu"] == "istikrarli"

    def test_tek_yil_none(self):
        assert _degerlendir({"trend": [{"yil": 2025, "yuzdelik": 0.5}]})["trend_yonu"] is None

    def test_orijinali_mutasyona_ugratmaz(self):
        kaynak = {"trend": [{"yil": 2025, "yuzdelik": 1.0}, {"yil": 2024, "yuzdelik": 2.0}]}
        _degerlendir(kaynak)
        assert "trend_yonu" not in kaynak


class TestLgsOneri:
    def _svc(self, monkeypatch):
        monkeypatch.setattr(lgs_mod, "_load", lambda: FAKE_LGS)
        return LgsService()

    def test_kovalar(self, monkeypatch):
        r = self._svc(monkeypatch).oneri(2.0)
        assert [x["okul"] for x in r["guvenli"]] == ["Kolay Lisesi"]
        assert [x["okul"] for x in r["tutar"]] == ["Sınır Lisesi"]
        assert [x["okul"] for x in r["riskli"]] == ["Zor Lisesi"]
        assert r["sayilar"] == {"guvenli": 1, "tutar": 1, "riskli": 1}

    def test_il_filtresi_fold(self, monkeypatch):
        # ascii küçük harf girilse de İSTANBUL eşleşir (İ/I tuzağı)
        r = self._svc(monkeypatch).oneri(2.0, il="istanbul")
        tum = r["guvenli"] + r["tutar"] + r["riskli"]
        assert all(x["il"] == "İSTANBUL" for x in tum) and len(tum) == 3

    def test_ilce_filtresi(self, monkeypatch):
        r = self._svc(monkeypatch).oneri(2.0, il="İSTANBUL", ilce="Kadıköy")
        tum = r["guvenli"] + r["tutar"] + r["riskli"]
        assert {x["ilce"] for x in tum} == {"KADIKÖY"}

    def test_tur_filtresi(self, monkeypatch):
        r = self._svc(monkeypatch).oneri(2.0, turler=["fen"])
        assert r["sayilar"]["guvenli"] == 0  # Kolay Lisesi anadolu — elendi

    def test_ilceler(self, monkeypatch):
        assert self._svc(monkeypatch).ilceler("istanbul") == ["BEŞİKTAŞ", "KADIKÖY"]


def _prog(dal, kurum, tur, min_puan):
    return {
        "kod": "111000101", "ad": f"{kurum}/{dal}", "kurum": kurum, "dal": dal,
        "kontenjan_turu": tur, "kontenjan": 5, "yerlesen": 5, "bos": 0,
        "min_puan": min_puan, "max_puan": (min_puan + 5) if min_puan else None,
    }


FAKE_TUS = {
    "sinav": "TUS", "donem": "2025 1. Dönem", "guncelleme": "2025",
    "kaynak": "test", "kaynak_url": "test", "toplam": 5, "taban_puanli": 5,
    "programlar": [
        # Aday puanı 50 için: diff = 50 - taban
        _prog("ACİL TIP", "A Üni", "Genel", 47.0),        # diff 3 → güvenli
        _prog("ADLİ TIP", "B Üni", "Genel", 50.5),        # diff -0.5 → tutar
        _prog("ANATOMİ", "C Üni", "Genel", 53.0),         # diff -3 → riskli
        _prog("KARDİYOLOJİ", "D Üni", "Genel", 56.0),     # diff -6 → kapsam dışı
        # Yabancı Uyruklu — varsayılanda GÖRÜNMEMELİ
        _prog("ACİL TIP", "E Üni", "Yabancı Uyruklu", 45.0),
    ],
}


class TestTusOneri:
    def _svc(self, monkeypatch, data=FAKE_TUS):
        monkeypatch.setattr(tus_mod, "_load", lambda sinav: data)
        return TusService()

    def test_kovalar_ve_yu_varsayilan_dislama(self, monkeypatch):
        r = self._svc(monkeypatch).oneri(50.0, sinav="TUS")
        assert [x["dal"] for x in r["guvenli"]] == ["ACİL TIP"]
        assert [x["dal"] for x in r["tutar"]] == ["ADLİ TIP"]
        assert [x["dal"] for x in r["riskli"]] == ["ANATOMİ"]
        tum = r["guvenli"] + r["tutar"] + r["riskli"]
        assert all(p["kontenjan_turu"] == "Genel" for p in tum)  # YU sızmadı

    def test_yu_acikca_istenince(self, monkeypatch):
        r = self._svc(monkeypatch).oneri(50.0, kontenjan_turu="Yabancı Uyruklu")
        tum = r["guvenli"] + r["tutar"] + r["riskli"]
        assert len(tum) == 1 and tum[0]["kurum"] == "E Üni"

    def test_dal_filtresi_fold(self, monkeypatch):
        r = self._svc(monkeypatch).oneri(50.0, dal="acil tıp")
        tum = r["guvenli"] + r["tutar"] + r["riskli"]
        assert len(tum) == 1 and tum[0]["dal"] == "ACİL TIP"

    def test_veri_yokken_guvenli_varsayilanlar(self, monkeypatch):
        svc = self._svc(monkeypatch, data={"programlar": []})
        m = svc.meta("DUS")
        assert m["sinav"] == "DUS" and m["donem"] == "" and m["dallar"] == []
        r = svc.oneri(50.0, sinav="DUS")
        assert r["sinav"] == "DUS" and r["sayilar"] == {"guvenli": 0, "tutar": 0, "riskli": 0}
