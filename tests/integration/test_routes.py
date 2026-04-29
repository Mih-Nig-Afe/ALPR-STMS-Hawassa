from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_redirects_to_login() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"


def test_login_page_renders() -> None:
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert "Phase 1 Operations" in response.text


def test_liveness_probe() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
