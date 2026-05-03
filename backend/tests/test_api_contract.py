from collections.abc import Callable

from fastapi.testclient import TestClient


def test_versioned_routes_exist_for_core_resources(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory() as client:
        home = create_home_api(client)

        responses = [
            client.get("/api/v1/health"),
            client.get("/api/v1/homes"),
            client.get(f"/api/v1/homes/{home['id']}"),
            client.get(f"/api/v1/homes/{home['id']}/chat"),
        ]

    assert [response.status_code for response in responses] == [200, 200, 200, 200]


def test_unversioned_routes_are_not_registered(
    client_factory: Callable[..., TestClient],
    create_home_api: Callable[..., dict[str, object]],
) -> None:
    with client_factory() as client:
        home = create_home_api(client)

        responses = [
            client.get("/api/health"),
            client.get("/api/homes"),
            client.get(f"/api/homes/{home['id']}"),
            client.get(f"/api/homes/{home['id']}/advice"),
            client.get(f"/api/homes/{home['id']}/chat"),
        ]

    assert [response.status_code for response in responses] == [404, 404, 404, 404, 404]
    assert {response.json()["error"]["code"] for response in responses} == {"not_found"}

