"""Ranking domain modeli — yıllık taban puan ve sıralama."""
from __future__ import annotations

from pydantic import BaseModel, Field

from unisense.domain.enums import ScoreType


class Ranking(BaseModel):
    """Bir üniversite + bölüm + yıl için sıralama kaydı."""

    year: int = Field(..., description="Yerleştirme yılı, örn: 2024")
    department_code: str
    university_code: str

    # Puan ve sıralama
    score_type: ScoreType
    base_score: float | None = Field(None, description="En düşük (taban) puan")
    top_score: float | None = Field(None, description="En yüksek (tavan) puan")
    base_rank: int | None = Field(None, description="Başarı sırası (taban)")
    top_rank: int | None = Field(None, description="Başarı sırası (tavan)")

    # Kontenjan
    quota: int | None = None
    placed: int | None = Field(None, description="Yerleşen sayısı")

    # Burs (vakıf üniversiteleri için)
    is_scholarship: bool = False
    scholarship_pct: int | None = None  # %25, %50, %75, %100

    # Kaynak
    source: str = "ÖSYM"
    source_url: str = ""


class RankingRange(BaseModel):
    """Sıralama aralığı — kullanıcıya gösterilecek özet."""
    department_code: str
    university_code: str
    department_name: str
    university_name: str
    year: int
    score_type: ScoreType
    rank_min: int | None = None  # en iyi (en küçük sayı)
    rank_max: int | None = None  # en kötü (en büyük sayı)
    score_min: float | None = None  # taban puan
    score_max: float | None = None  # tavan puan
