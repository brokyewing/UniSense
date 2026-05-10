"""UniSense domain enums."""
from __future__ import annotations
from enum import StrEnum


class UniversityType(StrEnum):
    """Üniversite türü."""
    DEVLET = "Devlet"
    VAKIF = "Vakıf"
    KKTC = "KKTC"
    YABANCI = "Yabancı"


class ScoreType(StrEnum):
    """YKS puan türü."""
    SAY = "SAY"      # Sayısal
    SOZ = "SÖZ"      # Sözel
    EA = "EA"        # Eşit Ağırlık
    DIL = "DİL"      # Yabancı Dil
    TYT = "TYT"      # Temel Yeterlilik
    SPECIAL = "ÖZEL" # Özel yetenek


class FacultyKind(StrEnum):
    """Fakülte/Yüksekokul türü."""
    FAKULTE = "Fakülte"
    YUKSEKOKUL = "Yüksekokul"
    MYO = "Meslek Yüksekokulu"
    ENSTITU = "Enstitü"
    KONSERVATUVAR = "Konservatuvar"


class EducationLevel(StrEnum):
    """Eğitim derecesi."""
    LISANS = "Lisans"           # 4 yıl
    ON_LISANS = "Ön Lisans"     # 2 yıl
    YUKSEK_LISANS = "Yüksek Lisans"
    DOKTORA = "Doktora"


class EducationLanguage(StrEnum):
    """Eğitim dili."""
    TR = "Türkçe"
    EN = "İngilizce"
    TR_EN = "Türkçe (%30 İng)"
    DE = "Almanca"
    FR = "Fransızca"
    AR = "Arapça"


class QueryIntent(StrEnum):
    """Kullanıcı sorgu niyeti — ileride router için."""
    DEPARTMENT_INFO = "department_info"        # "Bilgisayar müh nedir"
    UNI_RANKING = "uni_ranking"                # "İTÜ sıralamaları"
    DEPT_RANKING = "dept_ranking"              # "Bilgisayar müh sıralama"
    BY_SCORE = "by_score"                      # "300k puanım var"
    BY_CITY = "by_city"                        # "İstanbul'da hangi üni"
    BY_FACULTY = "by_faculty"                  # "Denizcilik fakültesi"
    COMPARE = "compare"                        # "İTÜ vs Boğaziçi"
    GENERAL = "general"                        # "tercih nasıl yapılır"
