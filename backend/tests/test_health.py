"""
Tests for the Phase 1 health endpoint.

Per ARCHITECTURE.md §102, Phase 1's definition of done includes
"Health check passes" and "Tests run" — this module covers both.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] in {"ok", "unavailable"}


@pytest.mark.asyncio
async def test_health_endpoint_mounted_under_api_prefix() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["success"] is True
