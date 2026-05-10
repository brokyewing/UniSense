"""Department / Faculty domain modeli."""
from __future__ import annotations

from pydantic import BaseModel, Field

from unisense.domain.enums import (
    EducationLanguage,
    EducationLevel,
    FacultyKind,
    ScoreType,
)


class Faculty(BaseModel):
    """Fakülte/Yüksekokul kaydı (üniversitenin alt birimi)."""
    code: str
    name: str = Field(..., description="'Bilgisayar ve Bilişim Fakültesi'")
    kind: FacultyKind = FacultyKind.FAKULTE
    university_code: str
    department_codes: list[str] = Field(default_factory=list)


class Department(BaseModel):
    """Bölüm kaydı — üniversite × bölüm × fakülte."""

    code: str = Field(..., description="ÖSYM bölüm kodu, örn: 100110085")
    name: str = Field(..., description="'Bilgisayar Mühendisliği'")
    faculty_code: str
    university_code: str
    score_type: ScoreType = ScoreType.SAY
    education_level: EducationLevel = EducationLevel.LISANS
    education_language: EducationLanguage = EducationLanguage.TR
    duration_years: int = 4

    # Akreditasyon, kontenjan, vb.
    accreditation: list[str] = Field(default_factory=list, description="MUDEK, EPDAD vs.")
    quota: int | None = Field(None, description="2025 kontenjan")
    description: str = ""
    description_url: str = ""
