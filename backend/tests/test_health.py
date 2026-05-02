from fastapi.testclient import TestClient
from httpx import Response

from app.main import create_app


def test_health_endpoint_returns_configured_provider_and_model() -> None:
    client = TestClient(app=create_app())

    response: Response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "provider": "local",
        "model": "local-model",
        "api_version": "v1",
    }


def test_unversioned_health_endpoint_is_not_registered() -> None:
    client = TestClient(create_app())

    response: Response = client.get(url="/api/health")

    assert response.status_code == 404
