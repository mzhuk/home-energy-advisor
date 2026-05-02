from app.db.connection import connect

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS homes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        build_period TEXT NOT NULL,
        home_size TEXT NOT NULL,
        residents TEXT NOT NULL,
        heating_system TEXT NOT NULL,
        has_ev INTEGER NOT NULL CHECK (has_ev IN (0, 1)),
        ai_context_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS advice (
        id TEXT PRIMARY KEY,
        home_id TEXT NOT NULL,
        summary TEXT NOT NULL,
        areas_json TEXT NOT NULL,
        disclaimer TEXT NOT NULL,
        provider TEXT NOT NULL,
        used_fallback INTEGER NOT NULL CHECK (used_fallback IN (0, 1)),
        created_at TEXT NOT NULL,
        FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_advice_home_created_at
    ON advice(home_id, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        home_id TEXT NOT NULL,
        role TEXT NOT NULL,
        source TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chat_messages_home_created_at
    ON chat_messages(home_id, created_at ASC)
    """,
    """
    CREATE TABLE IF NOT EXISTS llm_audit_events (
        id TEXT PRIMARY KEY,
        home_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        source TEXT NOT NULL,
        severity TEXT NOT NULL,
        original_text_hash TEXT,
        details_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (home_id) REFERENCES homes(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_llm_audit_events_home_created_at
    ON llm_audit_events(home_id, created_at DESC)
    """,
)


def init_schema(database_url: str) -> None:
    with connect(database_url) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()

