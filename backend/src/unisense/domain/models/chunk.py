"""ChromaDB için chunk modeli — RAG retrieval'da kullanılır."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """ChromaDB'de saklanan bilgi parçası."""

    chunk_id: str
    content: str = Field(..., min_length=20, max_length=5000)

    # UniSense'e özel metadata
    chunk_type: str = "general"           # general, university, department, ranking, faq
    university_code: str = ""              # ilgili üniversite (varsa)
    department_code: str = ""              # ilgili bölüm (varsa)
    score_type: str = ""                   # SAY/SÖZ/EA/DİL
    year: int | None = None                # ranking yılı
    city: str = ""

    heading: str = ""
    source: str = "Unknown"                # YÖK Atlas / ÖSYM / Üniversite sitesi
    source_url: str = ""
    language: str = "tr"
    distance: float | None = None
