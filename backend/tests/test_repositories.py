import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.advice.repository import get_latest_advice, save_advice
from app.chat.repository import append_message, list_messages
from app.core.settings import Settings
from app.db.connection import connect, sqlite_path_from_url
from app.db.ids import new_id
from app.db.json import dumps_json, loads_json
from app.db.schema import init_schema
from app.guardrails.audit_repository import append_audit_event, list_audit_events
from app.homes.repository import create_home, get_home, list_homes, touch_home
from app.main import create_app


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


def test_sqlite_path_from_url_supports_relative_absolute_and_memory() -> None:
    assert sqlite_path_from_url("sqlite:///./demo.db") == "./demo.db"
    assert sqlite_path_from_url("sqlite:////tmp/demo.db") == "/tmp/demo.db"
    assert sqlite_path_from_url("sqlite:///:memory:") == ":memory:"


def test_json_helpers_round_trip_deterministically() -> None:
    value = {"b": 2, "a": [{"z": True}]}

    encoded = dumps_json(value)

    assert encoded == '{"a":[{"z":true}],"b":2}'
    assert loads_json(encoded) == value


def test_new_id_adds_prefix() -> None:
    generated = new_id("home")

    assert generated.startswith("home_")
    assert len(generated) > len("home_")


def test_init_schema_creates_expected_tables(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "schema.db")

    init_schema(database_url)

    with connect(database_url) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }

    assert {"homes", "advice", "chat_messages", "llm_audit_events"}.issubset(tables)


def test_app_startup_initializes_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "startup.db"
    settings = Settings(database_url=sqlite_url(database_path))

    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert database_path.exists()


def test_repositories_round_trip_home_advice_chat_and_audit(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "repositories.db")
    init_schema(database_url)

    with connect(database_url) as connection:
        home = create_home(
            connection,
            {
                "id": "home_test",
                "name": "Main house",
                "build_period": "pre_1978",
                "home_size": "y100_200",
                "residents": "three_four",
                "heating_system": "gas",
                "has_ev": True,
                "ai_context": ["Context A", "Context B"],
            },
        )

        assert home["id"] == "home_test"
        assert home["has_ev"] is True
        assert home["ai_context"] == ["Context A", "Context B"]
        persisted_home = get_home(connection, "home_test")
        assert persisted_home is not None
        assert persisted_home["name"] == "Main house"

        second_home = create_home(
            connection,
            {
                "id": "home_second",
                "name": "Second house",
                "build_period": "post_2000",
                "home_size": "under_100",
                "residents": "one_two",
                "heating_system": "heat_pump",
                "has_ev": False,
                "ai_context": ["Context C"],
            },
        )
        touch_home(connection, str(second_home["id"]))

        assert [listed["id"] for listed in list_homes(connection)][0] == "home_second"

        advice = save_advice(
            connection,
            {
                "id": "advice_test",
                "home_id": "home_test",
                "summary": "Start with heat pump readiness.",
                "areas": [{"area_id": "heat_pump", "priority": "high"}],
                "disclaimer": "Directional advice only.",
                "provider": "fake",
                "used_fallback": False,
            },
        )

        assert advice["areas"] == [{"area_id": "heat_pump", "priority": "high"}]
        assert advice["used_fallback"] is False
        latest_advice = get_latest_advice(connection, "home_test")
        assert latest_advice is not None
        assert latest_advice["id"] == "advice_test"

        append_message(
            connection,
            {
                "id": "msg_user",
                "home_id": "home_test",
                "role": "user",
                "source": "solar",
                "content": "Are smaller panels useful?",
                "created_at": "2026-01-01T00:00:00+00:00",
            },
        )
        append_message(
            connection,
            {
                "id": "msg_assistant",
                "home_id": "home_test",
                "role": "assistant",
                "source": "solar",
                "content": "They can help with complex roof shapes.",
                "created_at": "2026-01-01T00:00:01+00:00",
            },
        )

        messages = list_messages(connection, "home_test")
        assert [message["id"] for message in messages] == ["msg_user", "msg_assistant"]

        audit_event = append_audit_event(
            connection,
            {
                "id": "audit_test",
                "home_id": "home_test",
                "event_type": "pii_scrubbed",
                "source": "global",
                "severity": "info",
                "original_text_hash": "hash",
                "details": {"entities": ["EMAIL_ADDRESS"]},
            },
        )

        assert audit_event["details"] == {"entities": ["EMAIL_ADDRESS"]}
        assert list_audit_events(connection, "home_test")[0]["id"] == "audit_test"


def test_foreign_keys_are_enforced(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "foreign_keys.db")
    init_schema(database_url)

    with connect(database_url) as connection:
        try:
            save_advice(
                connection,
                {
                    "id": "advice_orphan",
                    "home_id": "home_missing",
                    "summary": "Nope.",
                    "areas": [],
                    "disclaimer": "Nope.",
                    "provider": "fake",
                    "used_fallback": False,
                },
            )
        except sqlite3.IntegrityError:
            return

    raise AssertionError("Expected foreign key violation.")
