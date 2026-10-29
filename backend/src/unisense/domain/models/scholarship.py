"""Burs ve öğrenim ücreti veri modelleri."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ScholarshipInfo(BaseModel):
    """Bir programın burs/ücret bilgisi."""
    program_code: str
    university_name: str
    department_name: str
    year: int  # hangi yılın verisi
    university_type: str  # Devlet, Vakıf, KKTC
    fee_try: int | None = None  # yıllık öğrenim ücreti (TL)
    scholarship_rate: float | None = None  # burs oranı (0-100, %)
    scholarship_type: str | None = None  # tam burs, %50 burs, %25 burs, vb.
    notes: str | None = None


class ScholarshipListResponse(BaseModel):
    """Burs/ücret listesi response."""
    year: int
    items: list[ScholarshipInfo]
    total: int
    not_: str | None = Field(default=None, alias="not")