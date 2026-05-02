import hashlib
import sqlite3
from typing import Any

from app.db.ids import new_id
from app.guardrails.audit_repository import append_audit_event
from app.guardrails.models import GuardrailEventType, GuardrailSeverity


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_audit_event(
    connection: sqlite3.Connection,
    *,
    home_id: str,
    event_type: GuardrailEventType,
    source: str,
    severity: GuardrailSeverity,
    original_text: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_audit_event(
        connection,
        {
            "id": new_id("audit"),
            "home_id": home_id,
            "event_type": event_type.value,
            "source": source,
            "severity": severity.value,
            "original_text_hash": text_hash(original_text) if original_text else None,
            "details": _safe_details(details or {}),
        },
    )


def _safe_details(details: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in details.items():
        if key in {"text", "message", "prompt", "content", "raw"}:
            safe[key] = "[redacted]"
        else:
            safe[key] = value
    return safe

