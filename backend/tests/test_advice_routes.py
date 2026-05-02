from pathlib import Path

from fastapi.testclient import TestClient
from httpx import Response

from app.core.settings import LLMProvider, Settings
from app.main import create_app


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


def create_client(tmp_path: Path, *, llm_provider: LLMProvider = "local") -> TestClient:
    settings = Settings(
        database_url=sqlite_url(tmp_path / "advice.db"),
        llm_provider=llm_provider,
    )
    return TestClient(create_app(settings))


def home_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Main house",
        "build_period": "pre_1978",
        "home_size": "y100_200",
        "residents": "three_four",
        "heating_system": "gas",
        "has_ev": True,
    }
    payload.update(overrides)
    return payload


def create_home(client: TestClient, **overrides: object) -> dict[str, object]:
    response: Response = client.post("/api/v1/homes", json=home_payload(**overrides))
    assert response.status_code == 201
    return response.json()


def test_get_advice_before_generation_returns_advice_not_found(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        home = create_home(client)

        response: Response = client.get(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "advice_not_found"
    assert body["error"]["request_id"]


def test_get_and_post_advice_for_missing_home_return_not_found(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        get_response: Response = client.get("/api/v1/homes/home_missing/advice")
        post_response: Response = client.post("/api/v1/homes/home_missing/advice")

    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "not_found"
    assert post_response.status_code == 404
    assert post_response.json()["error"]["code"] == "not_found"


def test_generate_advice_persists_deterministic_fallback_contract(tmp_path: Path) -> None:
    with create_client(tmp_path, llm_provider="fake") as client:
        home = create_home(client)

        response: Response = client.post(f"/api/v1/homes/{home['id']}/advice")
        latest_response: Response = client.get(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 201
    body = response.json()
    assert body == latest_response.json()
    assert body["id"].startswith("advice_")
    assert body["home_id"] == home["id"]
    assert body["provider"] == "fake"
    assert body["used_fallback"] is False
    assert body["summary"]
    assert body["disclaimer"]
    assert [area["area_id"] for area in body["areas"]] == [
        "solar",
        "battery",
        "heat_pump",
        "smart_controls",
        "ev_charging",
    ]
    assert body["areas"][2]["priority"] == "high"
    assert "Demo note" in body["disclaimer"]
    assert body["created_at"]


def test_generate_advice_omits_ev_area_for_non_ev_home(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        home = create_home(client, has_ev=False)

        response: Response = client.post(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 201
    assert "ev_charging" not in [area["area_id"] for area in response.json()["areas"]]


def test_generate_advice_repeatedly_updates_latest_advice(tmp_path: Path) -> None:
    with create_client(tmp_path) as client:
        home = create_home(client)

        first = client.post(f"/api/v1/homes/{home['id']}/advice").json()
        second = client.post(f"/api/v1/homes/{home['id']}/advice").json()
        latest = client.get(f"/api/v1/homes/{home['id']}/advice").json()

    assert first["id"] != second["id"]
    assert latest["id"] == second["id"]
    assert latest["areas"] == second["areas"]


def test_home_detail_includes_latest_advice_after_generation(tmp_path: Path) -> None:
    with create_client(tmp_path, llm_provider="fake") as client:
        home = create_home(client)
        generated = client.post(f"/api/v1/homes/{home['id']}/advice").json()

        response: Response = client.get(f"/api/v1/homes/{home['id']}")

    assert response.status_code == 200
    assert response.json()["latest_advice"]["id"] == generated["id"]
    assert response.json()["latest_advice"]["provider"] == "fake"
