"""
Backend API Tests — pytest with httpx async client
"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client."""
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


@pytest.mark.anyio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "version" in resp.json()


@pytest.mark.anyio
async def test_health_endpoint(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.anyio
async def test_list_logs_empty(client):
    resp = await client.get("/api/v1/logs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_list_results_empty(client):
    resp = await client.get("/api/v1/results")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_analyze_missing_log(client):
    resp = await client.post(
        "/api/v1/analyze",
        json={"log_ids": ["nonexistent-id"], "mode": "auto", "sensitivity": 7},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_dashboard_stats(client):
    resp = await client.get("/api/v1/stats/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_logs" in data
    assert "total_analyses" in data
    assert "total_anomalies" in data
