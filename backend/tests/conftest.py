from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.core.settings import LLMProvider, Settings
from app.homes.schemas import BuildPeriod, HeatingSystem, HomeProfile, HomeSize, Residents
from app.main import create_app


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path}"


@pytest.fixture
def settings_factory(tmp_path: Path) -> Callable[..., Settings]:
    def build_settings(
        *,
        name: str = "test.db",
        llm_provider: LLMProvider = "fake",
    ) -> Settings:
        return Settings(
            database_url=sqlite_url(tmp_path / name),
            llm_provider=llm_provider,
        )

    return build_settings


@pytest.fixture
def client_factory(settings_factory: Callable[..., Settings]) -> Callable[..., TestClient]:
    def build_client(
        *,
        name: str = "test.db",
        llm_provider: LLMProvider = "fake",
    ) -> TestClient:
        return TestClient(create_app(settings_factory(name=name, llm_provider=llm_provider)))

    return build_client


@pytest.fixture
def default_home_payload() -> dict[str, object]:
    return {
        "name": "Main house",
        "build_period": "pre_1978",
        "home_size": "y100_200",
        "residents": "three_four",
        "heating_system": "gas",
        "has_ev": True,
    }


@pytest.fixture
def home_payload_factory(
    default_home_payload: dict[str, object],
) -> Callable[..., dict[str, object]]:
    def build_payload(**overrides: object) -> dict[str, object]:
        payload = default_home_payload.copy()
        payload.update(overrides)
        return payload

    return build_payload


@pytest.fixture
def create_home_api(
    home_payload_factory: Callable[..., dict[str, object]],
) -> Callable[..., dict[str, object]]:
    def create_home(client: TestClient, **overrides: object) -> dict[str, object]:
        response: Response = client.post("/api/v1/homes", json=home_payload_factory(**overrides))
        assert response.status_code == 201
        return response.json()

    return create_home


def home_profile_from_response(home: dict[str, object]) -> HomeProfile:
    return HomeProfile(
        id=str(home["id"]),
        name=str(home["name"]),
        build_period=BuildPeriod(str(home["build_period"])),
        home_size=HomeSize(str(home["home_size"])),
        residents=Residents(str(home["residents"])),
        heating_system=HeatingSystem(str(home["heating_system"])),
        has_ev=bool(home["has_ev"]),
        created_at=str(home["created_at"]),
        updated_at=str(home["updated_at"]),
    )


@pytest.fixture
def home_profile_from_response_factory() -> Callable[[dict[str, object]], HomeProfile]:
    return home_profile_from_response
