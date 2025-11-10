"""Basic health check tests for the API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that the health endpoint returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_root_redirect():
    """Test that root redirects to /ui/."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [301, 302, 307, 308]


@pytest.mark.asyncio
async def test_database_connection(db_session):
    """Test that database connection works."""
    assert db_session is not None
    # Basic database connection test
    result = await db_session.execute("SELECT 1")
    assert result is not None
