import sqlite3
from collections.abc import Mapping
from typing import Any

from app.db.json import dumps_json, loads_json
from app.db.time import utc_now_iso


def _advice_from_row(row: sqlite3.Row) -> dict[str, Any]:
    advice = dict(row)
    advice["used_fallback"] = bool(advice["used_fallback"])
    advice["areas"] = loads_json(advice.pop("areas_json"))
    return advice


def save_advice(connection: sqlite3.Connection, advice: Mapping[str, Any]) -> dict[str, Any]:
    created_at = str(advice.get("created_at") or utc_now_iso())
    connection.execute(
        """
        INSERT INTO advice (
            id, home_id, summary, areas_json, disclaimer, provider, used_fallback, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            advice["id"],
            advice["home_id"],
            advice["summary"],
            dumps_json(advice["areas"]),
            advice["disclaimer"],
            advice["provider"],
            int(bool(advice["used_fallback"])),
            created_at,
        ),
    )
    connection.commit()
    latest = get_latest_advice(connection, str(advice["home_id"]))
    if latest is None:
        msg = "Advice creation failed."
        raise RuntimeError(msg)
    return latest


def get_latest_advice(connection: sqlite3.Connection, home_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT * FROM advice
        WHERE home_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (home_id,),
    ).fetchone()
    return _advice_from_row(row) if row else None

