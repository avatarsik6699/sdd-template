from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "connected"


async def test_health_sets_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers


async def test_health_respects_provided_request_id(client: AsyncClient) -> None:
    custom_id = "test-correlation-id-123"
    response = await client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.headers["x-request-id"] == custom_id
