"""Domain layer."""
from unisense.domain.enums import (
    EducationLanguage,
    EducationLevel,
    FacultyKind,
    QueryIntent,
    ScoreType,
    UniversityType,
)
from unisense.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    NotFoundError,
    PromptInjectionError,
    QuotaExceededError,
    RateLimitError,
    UpstreamError,
    ValidationError,
)
from unisense.domain.models import (
    Answer,
    Chunk,
    Department,
    Faculty,
    Query,
    Ranking,
    RankingRange,
    Recommendation,
    RecommendationList,
    StudentProfile,
    University,
)

__all__ = [
    "Answer", "AuthenticationError", "AuthorizationError",
    "Chunk", "Department", "DomainError",
    "EducationLanguage", "EducationLevel", "Faculty", "FacultyKind",
    "NotFoundError", "PromptInjectionError",
    "Query", "QueryIntent", "QuotaExceededError",
    "Ranking", "RankingRange", "RateLimitError",
    "Recommendation", "RecommendationList", "ScoreType",
    "StudentProfile", "University", "UniversityType",
    "UpstreamError", "ValidationError",
]
