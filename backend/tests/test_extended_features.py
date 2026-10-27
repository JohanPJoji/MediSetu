import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_extended_routes_are_mounted(client: AsyncClient):
    paths = (await client.get("/openapi.json")).json()["paths"]
    assert "/api/laboratory/tests" in paths
    assert "/api/laboratory/orders" in paths
    assert "/api/billing" in paths
    assert "/api/billing/payments" in paths
    assert "/api/inventory/batches" in paths
    assert "/api/alerts/medicine-alerts" in paths

@pytest.mark.asyncio
async def test_extended_routes_require_auth(client: AsyncClient):
    for path in ("/api/laboratory/tests", "/api/laboratory/orders", "/api/billing", "/api/inventory/batches", "/api/alerts/medicine-alerts"):
        response = await client.get(path)
        assert response.status_code == 401, (path, response.text)
