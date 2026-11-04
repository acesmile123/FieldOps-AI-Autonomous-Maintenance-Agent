from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import engine
from app.main import app


def test_health_and_sqlite_connection():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "fieldops-api"
    assert isinstance(body["demo_mock_mode"], bool)
    assert isinstance(body["meta_key_configured"], bool)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_cors_allowed_origin():
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
