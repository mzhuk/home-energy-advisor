from collections.abc import Callable, Sequence

from fastapi.testclient import TestClient
from httpx import Response
from pytest_mock import MockerFixture

from app.advice.deterministic import build_deterministic_advice
from app.core.errors import LLMUnavailableError
from app.homes.schemas import HomeProfile
from app.llm.client import LLMMessage


class StubLLMClient:
    def __init__(self, responses: Sequence[str | Exception]) -> None:
        self.responses = list(responses)
        self.calls: list[list[LLMMessage]] = []

    def generate_advice(
        self, messages: Sequence[LLMMessage], response_schema: dict[str, object]
    ) -> str:
        self.calls.append(list(messages))
        _ = response_schema
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def chat(self, messages: Sequence[LLMMessage], *, source: str = "global") -> str:
        _ = messages
        _ = source
        return "ok"


def test_get_advice_before_generation_returns_advice_not_found(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory(name="advice.db") as client:
        home = create_home_api(client)

        response: Response = client.get(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "advice_not_found"
    assert body["error"]["request_id"]


def test_get_and_post_advice_for_missing_home_return_not_found(
    client_factory: Callable[..., TestClient],
) -> None:
    with client_factory(name="advice.db") as client:
        get_response: Response = client.get("/api/v1/homes/home_missing/advice")
        post_response: Response = client.post("/api/v1/homes/home_missing/advice")

    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "not_found"
    assert post_response.status_code == 404
    assert post_response.json()["error"]["code"] == "not_found"


def test_generate_advice_persists_deterministic_fallback_contract(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory(name="advice.db", llm_provider="fake") as client:
        home = create_home_api(client)

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


def test_generate_advice_omits_ev_area_for_non_ev_home(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory(name="advice.db") as client:
        home = create_home_api(client, has_ev=False)

        response: Response = client.post(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 201
    assert "ev_charging" not in [area["area_id"] for area in response.json()["areas"]]


def test_generate_advice_repeatedly_updates_latest_advice(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory(name="advice.db") as client:
        home = create_home_api(client)

        first = client.post(f"/api/v1/homes/{home['id']}/advice").json()
        second = client.post(f"/api/v1/homes/{home['id']}/advice").json()
        latest = client.get(f"/api/v1/homes/{home['id']}/advice").json()

    assert first["id"] != second["id"]
    assert latest["id"] == second["id"]
    assert latest["areas"] == second["areas"]


def test_home_detail_includes_latest_advice_after_generation(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory(name="advice.db", llm_provider="fake") as client:
        home = create_home_api(client)
        generated = client.post(f"/api/v1/homes/{home['id']}/advice").json()

        response: Response = client.get(f"/api/v1/homes/{home['id']}")

    assert response.status_code == 200
    assert response.json()["latest_advice"]["id"] == generated["id"]
    assert response.json()["latest_advice"]["provider"] == "fake"


def test_local_provider_advice_success_uses_model_response(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
    home_profile_from_response_factory: Callable[[dict[str, object]], HomeProfile],
    mocker: MockerFixture,
) -> None:
    with client_factory(name="advice.db", llm_provider="local") as client:
        home = create_home_api(client)
        advice_json = build_deterministic_advice(
            home_profile_from_response_factory(home),
            ai_context=["context"],
        ).model_dump_json()
        stub = StubLLMClient([advice_json])
        mocker.patch("app.advice.service.create_llm_client", return_value=stub)

        response: Response = client.post(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "local"
    assert body["used_fallback"] is False
    assert len(stub.calls) == 1
    assert "Return valid JSON only" in stub.calls[0][1].content


def test_local_provider_advice_falls_back_after_invalid_model_response(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
    mocker: MockerFixture,
) -> None:
    with client_factory(name="advice.db", llm_provider="local") as client:
        home = create_home_api(client)
        stub = StubLLMClient(["not json"])
        mocker.patch("app.advice.service.create_llm_client", return_value=stub)

        response: Response = client.post(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 201
    body = response.json()
    assert body["used_fallback"] is True
    assert body["summary"].startswith("Start with heat pump readiness")
    assert len(stub.calls) == 1


def test_local_provider_advice_falls_back_after_provider_error(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
    mocker: MockerFixture,
) -> None:
    with client_factory(name="advice.db", llm_provider="local") as client:
        home = create_home_api(client)
        stub = StubLLMClient([LLMUnavailableError()])
        mocker.patch("app.advice.service.create_llm_client", return_value=stub)

        response: Response = client.post(f"/api/v1/homes/{home['id']}/advice")

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "local"
    assert body["used_fallback"] is True
    assert body["summary"].startswith("Start with heat pump readiness")
