from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def _login(c: TestClient, username: str, password: str) -> None:
    c.cookies.clear()
    response = c.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text


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


def test_unknown_route_renders_html_404_for_browser() -> None:
    response = client.get("/this-page-does-not-exist", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "Page not found" in body
    assert "error-code" in body
    assert "Skip to main content" in body


def test_unknown_route_returns_json_for_api_clients() -> None:
    response = client.get("/this-page-does-not-exist", headers={"accept": "application/json"})
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]
    assert response.json()["detail"] == "Not Found"


def test_health_ready_returns_json_even_with_html_accept() -> None:
    response = client.get("/health/ready", headers={"accept": "text/html"})
    assert "application/json" in response.headers["content-type"]


def test_traffic_officer_admin_access_denied_html() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "TP1", settings.officer_default_password)
        response = c.get("/admin", headers={"accept": "text/html"})
        assert response.status_code == 403
        body = response.text
        assert "Access denied" in body or "Insufficient role" in body
        assert "error-code" in body


def test_violations_filter_renders_status_options() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "TP1", settings.officer_default_password)
        response = c.get("/violations?status=REPORTED")
        assert response.status_code == 200
        body = response.text
        assert "filter-bar" in body
        assert 'value="REPORTED"' in body
        assert "selected" in body


def test_admin_dashboard_renders_users_and_subcities() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "ADMIN1", settings.admin_default_password)
        response = c.get("/admin")
        assert response.status_code == 200
        body = response.text
        for marker in ("Admin overview", "Users", "Subcities", "Recent audit", "stat-panel"):
            assert marker in body, marker


def test_alerts_listing_uses_status_badge_macro() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "ADMIN1", settings.admin_default_password)
        response = c.get("/alerts")
        assert response.status_code == 200
        body = response.text
        assert "filter-bar" in body
        assert "All statuses" in body


def test_complaints_listing_renders_queue_filters() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "CO1", settings.complaint_default_password)
        response = c.get("/complaints?status=OPEN")
        assert response.status_code == 200
        body = response.text
        assert "Queue" in body
        assert "filter-bar" in body
        assert 'value="OPEN"' in body
        assert "selected" in body


def test_payments_listing_renders_request_filters() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "ADMIN1", settings.admin_default_password)
        response = c.get("/payments?status=REQUESTED")
        assert response.status_code == 200
        body = response.text
        assert "Requests" in body
        assert "filter-bar" in body
        assert 'value="REQUESTED"' in body
        assert "selected" in body


def test_404_error_page_keeps_logged_in_navigation() -> None:
    settings = get_settings()
    with TestClient(app) as c:
        _login(c, "ADMIN1", settings.admin_default_password)
        response = c.get("/does-not-exist", headers={"accept": "text/html"})
        assert response.status_code == 404
        body = response.text
        assert "Page not found" in body
        assert "Sign out" in body
        assert 'href="/admin"' in body
