from pathlib import Path

from fastapi.testclient import TestClient
from httpx import Response

from app.advice.repository import save_advice
from app.core.settings import Settings
from app.db.connection import connect
from app.homes.ai_context import build_ai_context
from app.homes.schemas import BuildPeriod, HeatingSystem, HomeCreateRequest, HomeSize, Residents
from app.main import create_app


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


def create_client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=sqlite_url(tmp_path / "homes.db"))
    return TestClient(create_app(settings))


def valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": " Main house ",
        "build_period": "pre_1978",
        "home_size": "y100_200",
        "residents": "three_four",
        "heating_system": "gas",
        "has_ev": True,
    }
    payload.update(overrides)
    return payload


def test_create_home_trims_name_and_returns_ai_context(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response: Response = client.post("/api/v1/homes", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("home_")
    assert body["name"] == "Main house"
    assert body["build_period"] == "pre_1978"
    assert body["home_size"] == "y100_200"
    assert body["residents"] == "three_four"
    assert body["heating_system"] == "gas"
    assert body["has_ev"] is True
    assert body["latest_advice"] is None
    assert len(body["ai_context"]) == 5
    assert "weaker baseline efficiency" in body["ai_context"][0]
    assert "heat pump conversion as a major opportunity" in body["ai_context"][3]
    assert "Include EV charging" in body["ai_context"][4]
    assert body["created_at"]
    assert body["updated_at"]


def test_list_homes_returns_lightweight_profiles_in_latest_order(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        first = client.post("/api/v1/homes", json=valid_payload(name="First")).json()
        second = client.post("/api/v1/homes", json=valid_payload(name="Second")).json()

        response: Response = client.get("/api/v1/homes")

    assert response.status_code == 200
    homes = response.json()
    assert [home["id"] for home in homes] == [second["id"], first["id"]]
    assert "ai_context" not in homes[0]
    assert "latest_advice" not in homes[0]


def test_get_home_includes_latest_advice_when_available(tmp_path: Path) -> None:
    database_url = sqlite_url(tmp_path / "homes.db")
    settings = Settings(database_url=database_url)

    with TestClient(create_app(settings)) as client:
        created = client.post("/api/v1/homes", json=valid_payload()).json()
        with connect(database_url) as connection:
            save_advice(
                connection,
                {
                    "id": "advice_test",
                    "home_id": created["id"],
                    "summary": "Solar and heat pump readiness are the first priorities.",
                    "areas": [{"area_id": "solar", "priority": "high"}],
                    "disclaimer": "Directional advice only.",
                    "provider": "fake",
                    "used_fallback": False,
                },
            )

        response: Response = client.get(f"/api/v1/homes/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["latest_advice"]["id"] == "advice_test"
    assert body["latest_advice"]["used_fallback"] is False
    assert body["latest_advice"]["areas"] == [{"area_id": "solar", "priority": "high"}]


def test_missing_home_returns_standard_not_found_envelope(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response: Response = client.get("/api/v1/homes/home_missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["message"] == "Home profile was not found."
    assert response.json()["error"]["request_id"]


def test_blank_home_name_returns_validation_error_envelope(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response: Response = client.post("/api/v1/homes", json=valid_payload(name="   "))

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]["fields"][0]["loc"] == ["body", "name"]


def test_unknown_profile_enum_returns_validation_error_envelope(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        response: Response = client.post(
            "/api/v1/homes", json=valid_payload(build_period="ancient")
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_ai_context_mapping_covers_all_profile_answers() -> None:
    context = build_ai_context(
        HomeCreateRequest(
            name="In progress home",
            build_period=BuildPeriod.IN_PROGRESS,
            home_size=HomeSize.OVER_200,
            residents=Residents.FIVE_PLUS,
            heating_system=HeatingSystem.OTHER_UNKNOWN,
            has_ev=False,
        )
    )

    assert context == [
        (
            "Treat the home as a strong opportunity for integrated planning from the beginning. "
            "Prioritize solar readiness, battery placement, heat pump design, EV charging "
            "infrastructure, wiring, sensors, and smart control architecture."
        ),
        (
            "Assume higher demand and more complex energy management. Prioritize zoning, larger or "
            "staged heat pump planning, expanded solar potential, battery capacity analysis, and "
            "detailed monitoring."
        ),
        (
            "Assume high hot water, heating, appliance, and charging demand. Prioritize load "
            "management, smart controls, solar self-consumption, and battery usefulness."
        ),
        (
            "Ask clarifying questions when needed. Give cautious advice and focus on assessment "
            "steps before recommending specific heat pump changes."
        ),
        (
            "Do not center EV charging in recommendations. Mention EV readiness only as optional "
            "future-proofing when discussing solar, storage, or smart electrical planning."
        ),
    ]
