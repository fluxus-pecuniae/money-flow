"""Small security helpers for API/runtime safety surfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any


REDACTED_VALUE = "<redacted>"


class APIAuthScope(StrEnum):
    READ_ONLY_OPERATOR = "read_only_operator"
    OPERATOR = "operator"
    ADMIN = "admin"
    AUTOMATION_ADMIN = "automation_admin"
    UAT_ADMIN = "uat_admin"


@dataclass(frozen=True)
class APIPrincipal:
    principal_id: str
    scopes: frozenset[APIAuthScope]
    auth_mode: str

    def has_scope(self, required: APIAuthScope) -> bool:
        if APIAuthScope.ADMIN in self.scopes:
            return True
        if required == APIAuthScope.READ_ONLY_OPERATOR:
            return bool(
                self.scopes
                & {
                    APIAuthScope.READ_ONLY_OPERATOR,
                    APIAuthScope.OPERATOR,
                    APIAuthScope.AUTOMATION_ADMIN,
                    APIAuthScope.UAT_ADMIN,
                }
            )
        if required == APIAuthScope.OPERATOR:
            return bool(
                self.scopes
                & {
                    APIAuthScope.OPERATOR,
                    APIAuthScope.AUTOMATION_ADMIN,
                    APIAuthScope.UAT_ADMIN,
                }
            )
        if required == APIAuthScope.AUTOMATION_ADMIN:
            return APIAuthScope.AUTOMATION_ADMIN in self.scopes
        if required == APIAuthScope.UAT_ADMIN:
            return APIAuthScope.UAT_ADMIN in self.scopes
        return required in self.scopes


_SENSITIVE_KEY_MARKERS = (
    "api_key",
    "apikey",
    "api-secret",
    "api_secret",
    "authorization",
    "bearer",
    "credential",
    "jwt",
    "passphrase",
    "password",
    "private_key",
    "secret",
    "signing",
    "token",
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


_BEARER_RE = re.compile(r"(?i)(authorization:\s*bearer\s+|bearer\s+)([A-Za-z0-9._~+/=-]+)")
_KEY_VALUE_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|token|private[_-]?key|api[_-]?secret)=([^&\s,;]+)"
)
_POSTGRES_URL_PASSWORD_RE = re.compile(r"(postgresql(?:\+psycopg)?://[^:/@\s]+:)([^@\s]+)(@)")


def redact_sensitive_text(value: str) -> str:
    """Redact obvious secrets embedded inside free-form text."""

    redacted = _BEARER_RE.sub(lambda match: f"{match.group(1)}{REDACTED_VALUE}", value)
    redacted = _KEY_VALUE_SECRET_RE.sub(
        lambda match: f"{match.group(1)}={REDACTED_VALUE}",
        redacted,
    )
    redacted = _POSTGRES_URL_PASSWORD_RE.sub(
        lambda match: f"{match.group(1)}{REDACTED_VALUE}{match.group(3)}",
        redacted,
    )
    return redacted


def redact_sensitive_structure(value: Any) -> Any:
    """Return a copy with obvious secret-bearing fields redacted."""

    if isinstance(value, Mapping):
        return {
            key: REDACTED_VALUE if is_sensitive_key(str(key)) else redact_sensitive_structure(item)
            for key, item in value.items()
        }
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [redact_sensitive_structure(item) for item in value]
    return value


def redact_api_error_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Redact a representative API error payload before client/operator exposure."""

    return redact_sensitive_structure(dict(payload))


def redact_structured_log_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Redact a representative structured log event before rendering or persistence."""

    return redact_sensitive_structure(dict(event))
