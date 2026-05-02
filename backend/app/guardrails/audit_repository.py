import sqlite3
from collections.abc import Mapping
from typing import Any

from app.db.json import dumps_json, loads_json
from app.db.time import utc_now_iso


def _audit_event_from_row(row: sqlite3.Row) -> dict[str, Any]:
    event = dict(row)
    event["details"] = loads_json(event.pop("details_json"))
    return event


def append_audit_event(connection: sqlite3.Connection, event: Mapping[str, Any]) -> dict[str, Any]:
    created_at = str(event.get("created_at") or utc_now_iso())
    connection.execute(
        """
        INSERT INTO llm_audit_events (
            id, home_id, event_type, source, severity, original_text_hash, details_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["id"],
            event["home_id"],
            event["event_type"],
            event["source"],
            event["severity"],
            event.get("original_text_hash"),
            dumps_json(event["details"]),
            created_at,
        ),
    )
    connection.commit()
    return {
        "id": event["id"],
        "home_id": event["home_id"],
        "event_type": event["event_type"],
        "source": event["source"],
        "severity": event["severity"],
        "original_text_hash": event.get("original_text_hash"),
        "details": event["details"],
        "created_at": created_at,
    }


def list_audit_events(connection: sqlite3.Connection, home_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT * FROM llm_audit_events
        WHERE home_id = ?
        ORDER BY created_at DESC
        """,
        (home_id,),
    ).fetchall()
    return [_audit_event_from_row(row) for row in rows]
