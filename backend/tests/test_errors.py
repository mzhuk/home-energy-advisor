from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import NotFoundError
from app.main import create_app


def client_with_error_routes() -> TestClient:
    app: FastAPI = create_app()

    @app.get("/api/v1/test/app-error")
    def raise_app_error() -> None:
        raise NotFoundError("Test resource not found.")

    @app.get("/api/v1/test/validation")
    def validate_query(count: int) -> dict[str, int]:
        return {"count": count}

    @app.get("/api/v1/test/unexpected")
    def raise_unexpected_error() -> None:
        raise RuntimeError("secret internals should not be returned")

    return TestClient(app, raise_server_exceptions=False)


def test_app_error_uses_standard_error_envelope() -> None:
    client = client_with_error_routes()

    response = client.get("/api/v1/test/app-error")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Test resource not found."
    assert body["error"]["details"] == {}
    assert body["error"]["request_id"]


def test_validation_error_uses_standard_error_envelope() -> None:
    client = client_with_error_routes()

    response = client.get("/api/v1/test/validation", params={"count": "not-a-number"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "The request payload or parameters are invalid."
    assert body["error"]["request_id"]
    assert body["error"]["details"]["fields"][0]["loc"] == ["query", "count"]
    assert "not-a-number" not in str(body)


def test_http_404_uses_standard_error_envelope() -> None:
    client = client_with_error_routes()

    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["request_id"]


def test_unexpected_error_is_sanitized() -> None:
    client = client_with_error_routes()

    response = client.get("/api/v1/test/unexpected")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "An unexpected error occurred."
    assert "secret internals" not in str(body)
