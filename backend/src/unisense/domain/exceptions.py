"""Domain exceptions."""
from __future__ import annotations


class DomainError(Exception):
    code: str = "domain_error"
    http_status: int = 500

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainError):
    code = "not_found"
    http_status = 404


class ValidationError(DomainError):
    code = "validation_error"
    http_status = 422


class RateLimitError(DomainError):
    code = "rate_limited"
    http_status = 429


class UpstreamError(DomainError):
    code = "upstream_error"
    http_status = 502


class QuotaExceededError(UpstreamError):
    code = "quota_exceeded"
    http_status = 503


class AuthenticationError(DomainError):
    code = "auth_required"
    http_status = 401


class AuthorizationError(DomainError):
    code = "forbidden"
    http_status = 403


class PromptInjectionError(ValidationError):
    code = "prompt_injection_detected"
    http_status = 400
