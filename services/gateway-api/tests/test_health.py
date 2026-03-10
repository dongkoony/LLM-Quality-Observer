"""
Health check endpoint tests
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

for module_name in [name for name in list(sys.modules) if name == "app" or name.startswith("app.")]:
    sys.modules.pop(module_name)

from app.main import app

app.state.testing = True
client = TestClient(app)


def test_health_check():
    """Test that health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
