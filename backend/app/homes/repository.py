import sqlite3
from collections.abc import Mapping
from typing import Any

from app.db.json import dumps_json, loads_json
from app.db.time import utc_now_iso


def _home_from_row(row: sqlite3.Row) -> dict[str, Any]:
    home = dict(row)
    home["has_ev"] = bool(home["has_ev"])
    home["ai_context"] = loads_json(home.pop("ai_context_json"))
    return home


def create_home(connection: sqlite3.Connection, home: Mapping[str, Any]) -> dict[str, Any]:
    now = utc_now_iso()
    connection.execute(
        """
        INSERT INTO homes (
            id, name, build_period, home_size, residents, heating_system, has_ev,
            ai_context_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            home["id"],
            home["name"],
            home["build_period"],
            home["home_size"],
            home["residents"],
            home["heating_system"],
            int(bool(home["has_ev"])),
            dumps_json(home["ai_context"]),
            now,
            now,
        ),
    )
    connection.commit()
    created = get_home(connection, str(home["id"]))
    if created is None:
        msg = "Home creation failed."
        raise RuntimeError(msg)
    return created


def get_home(connection: sqlite3.Connection, home_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM homes WHERE id = ?", (home_id,)).fetchone()
    return _home_from_row(row) if row else None


def list_homes(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM homes ORDER BY updated_at DESC, created_at DESC"
    ).fetchall()
    return [_home_from_row(row) for row in rows]


def touch_home(connection: sqlite3.Connection, home_id: str) -> None:
    connection.execute(
        "UPDATE homes SET updated_at = ? WHERE id = ?",
        (utc_now_iso(), home_id),
    )
    connection.commit()
