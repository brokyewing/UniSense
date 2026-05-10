"""University domain modeli — bir üniversite kurumu."""
from __future__ import annotations

from pydantic import BaseModel, Field

from unisense.domain.enums import UniversityType


class University(BaseModel):
    """Üniversite kayıt modeli."""

    code: str = Field(..., description="ÖSYM/YÖK kısa kodu, örn: ITU, BOGAZICI")
    name: str = Field(..., description="Tam ad: 'İstanbul Teknik Üniversitesi'")
    short_name: str = Field("", description="Kısa ad: 'İTÜ'")
    type: UniversityType = UniversityType.DEVLET
    city: str = Field("", description="Şehir: 'İstanbul'")
    region: str = Field("", description="Bölge: 'Marmara'")
    founded_year: int | None = None
    student_count: int | None = None
    website: str = ""
    description: str = ""

    # Sıralama bilgileri (yıllık)
    urap_rank_tr: int | None = Field(None, description="URAP Türkiye sıralaması")
    qs_rank_world: int | None = Field(None, description="QS Dünya sıralaması")
    times_rank_world: int | None = Field(None, description="THE Dünya sıralaması")

    # İlgili faculty/department ID'leri
    faculty_codes: list[str] = Field(default_factory=list)

    class Config:
        frozen = False  # ranking'ler güncellenebilir
