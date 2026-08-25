"""Integration tests for authentication endpoints."""

from flask.testing import FlaskClient

from wedding_face_finder.models import User
from wedding_face_finder.utils.security import hash_password


class TestAuth:
    """Test suite for /api/admin/login and /api/admin/logout."""

    def test_login_success(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Valid credentials should create session."""
        user = User(
            username="admin",
            password_hash=hash_password("secret123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "secret123"},
        )
        assert resp.status_code == 200
        assert b"Login successful" in resp.data

    def test_login_wrong_password(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Wrong password should return 401."""
        user = User(
            username="admin",
            password_hash=hash_password("secret123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_missing_fields(self, client: FlaskClient) -> None:
        """Missing username or password should return 400."""
        resp = client.post("/api/admin/login", json={})
        assert resp.status_code == 400

    def test_logout_requires_login(self, client: FlaskClient) -> None:
        """Logout without session should return 401."""
        resp = client.post("/api/admin/logout")
        assert resp.status_code == 401

    def test_logout_success(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Logout should clear session after login."""
        user = User(
            username="admin",
            password_hash=hash_password("secret123"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "secret123"},
        )
        resp = client.post("/api/admin/logout")
        assert resp.status_code == 200
