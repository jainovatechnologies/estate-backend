import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    with patch("app.database.DatabaseManager.is_healthy", return_value=True):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"]["status"] == "connected"
        assert "timestamp" in data
        assert "llm_provider" in data


@pytest.mark.asyncio
async def test_health_degraded_when_db_down(async_client):
    with patch("app.database.DatabaseManager.is_healthy", return_value=False):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["database"]["status"] == "disconnected"
