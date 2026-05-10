"""LLM provider interface."""
from __future__ import annotations
from typing import Protocol


class LLMProvider(Protocol):
    @property
    def name(self) -> str: ...
    def is_available(self) -> bool: ...
    def generate(
        self,
        query: str,
        context: str | None = None,
        history: list[dict] | None = None,
    ) -> str: ...
