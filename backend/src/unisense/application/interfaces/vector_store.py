"""Vector store interface."""
from __future__ import annotations
from typing import Protocol

from unisense.domain.models import Chunk


class VectorStore(Protocol):
    def search(
        self,
        query: str,
        top_k: int = 6,
        filters: dict | None = None,
    ) -> list[Chunk]: ...
    def count(self) -> int: ...
