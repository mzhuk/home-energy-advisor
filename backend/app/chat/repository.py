import sqlite3
from collections.abc import Mapping
from typing import Any

from app.db.time import utc_now_iso


def append_message(connection: sqlite3.Connection, message: Mapping[str, Any]) -> dict[str, Any]:
    created_at = str(message.get("created_at") or utc_now_iso())
    connection.execute(
        """
        INSERT INTO chat_messages (id, home_id, role, source, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            message["id"],
            message["home_id"],
            message["role"],
            message["source"],
            message["content"],
            created_at,
        ),
    )
    connection.commit()
    return {
        "id": message["id"],
        "home_id": message["home_id"],
        "role": message["role"],
        "source": message["source"],
        "content": message["content"],
        "created_at": created_at,
    }


def list_messages(connection: sqlite3.Connection, home_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT * FROM chat_messages
        WHERE home_id = ?
        ORDER BY created_at ASC
        """,
        (home_id,),
    ).fetchall()
    return [dict(row) for row in rows]

