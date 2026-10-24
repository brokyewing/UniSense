"""Student profil ve tercih önerisi modelleri."""
from __future__ import annotations

from pydantic import BaseModel, Field

from unisense.domain.enums import ScoreType


class StudentProfile(BaseModel):
    """Tercih yapan öğrencinin profili."""
    score_type: ScoreType
    score: float | None = Field(None, description="YKS/AYT puanı")
    rank: int | None = Field(None, description="Başarı sırası")

    preferred_cities: list[str] = Field(default_factory=list)
    preferred_uni_types: list[str] = Field(default_factory=list, description="Devlet/Vakıf")
    preferred_languages: list[str] = Field(default_factory=list, description="Türkçe/İngilizce")
    preferred_departments: list[str] = Field(default_factory=list)

    # Önemler (1-5)
    importance_ranking: int = 3      # üni sıralaması ne kadar önemli
    importance_city: int = 3
    importance_scholarship: int = 3  # burs

    notes: str = ""


class Recommendation(BaseModel):
    """Tek bir tercih önerisi."""
    department_code: str
    university_code: str
    department_name: str
    university_name: str
    city: str
    score_type: ScoreType

    # Kullanıcının puanına göre
    fit_score: float = Field(..., ge=0, le=100, description="0-100 uygunluk")
    safety_level: str = Field(..., description="hedef / safe / reach (hedef üstü)")
    reason: str = ""
    placement_probability: float | None = Field(
        None, ge=0, le=1,
        description="Yerleşme olasılığı (0-1). Sigmoid: user_rank vs base_rank, q1 ile yumuşatma.",
    )

    # Referans veriler
    last_year_base_rank: int | None = None
    last_year_base_score: float | None = None
    quota: int | None = None

    # Kart zenginleştirme (öğrenci siteden çıkmasın): koşul/burs/dil/süre/trend
    scholarship: str = ""
    education_language: str = ""
    duration_years: int | None = None
    osym_conditions: list[str] = Field(default_factory=list)
    trend: list[dict] = Field(default_factory=list, description="Geçmiş yıl taban sırası/puanı (sparkline)")


class RecommendationList(BaseModel):
    """Önerilen tercihlerin tümü."""
    profile: StudentProfile
    safe: list[Recommendation] = Field(default_factory=list, description="Garanti")
    target: list[Recommendation] = Field(default_factory=list, description="Hedef")
    reach: list[Recommendation] = Field(default_factory=list, description="Hedef üstü")
    notes: str = ""
