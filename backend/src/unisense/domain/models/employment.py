"""Mezun istihdam veri modelleri."""
from __future__ import annotations

from pydantic import BaseModel


class EmploymentInfo(BaseModel):
    """Bir programın mezun istihdam bilgisi."""
    program_code: str
    department_name: str
    year: int  # hangi yılın verisi
    employment_rate: float | None = None  # iş bulma oranı (%)
    avg_salary_try: int | None = None  # ortalama maaş (TL)
    salary_range_min: int | None = None  # maaş aralığı min
    salary_range_max: int | None = None  # maaş aralığı max
    employment_sector: str | None = None  # istihdam sektörü
    top_employers: list[str] | None = None  # en çok işe alan kurumlar
    notes: str | None = None


class EmploymentListResponse(BaseModel):
    """İstihdam bilgisi listesi response."""
    year: int
    items: list[EmploymentInfo]
    total: int
    not_: str | None = None