"""UniSense domain models."""
from unisense.domain.models.chunk import Chunk
from unisense.domain.models.department import Department, Faculty
from unisense.domain.models.query import Answer, ChatTurn, Query
from unisense.domain.models.ranking import Ranking, RankingRange
from unisense.domain.models.student import Recommendation, RecommendationList, StudentProfile
from unisense.domain.models.university import University

__all__ = [
    "Answer",
    "ChatTurn",
    "Chunk",
    "Department",
    "Faculty",
    "Query",
    "Ranking",
    "RankingRange",
    "Recommendation",
    "RecommendationList",
    "StudentProfile",
    "University",
]
