"""
Health check endpoint tests
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
