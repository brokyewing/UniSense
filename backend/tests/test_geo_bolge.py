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
