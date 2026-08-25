"""Integration tests for download, admin, and status endpoints."""

import io
import zipfile

from flask.testing import FlaskClient

from wedding_face_finder.models import AuditLog, Event, Photo, User
from wedding_face_finder.utils.security import hash_password


class TestDownload:
    """Test suite for /api/download."""

    def _login(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Helper to create and login admin user."""
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

    def test_download_without_auth(self, client: FlaskClient) -> None:
        """Download without login should return 401."""
        resp = client.post("/api/download", json={"photo_ids": [1]})
        assert resp.status_code == 401

    def test_download_success(
        self,
        client: FlaskClient,
        db_session: object,
        tmp_path: object,
    ) -> None:
        """Valid download should return a ZIP."""
        self._login(client, db_session)

        event = Event(name="DL Event")
        db_session.add(event)
        db_session.commit()

        img_path = tmp_path / "dl.jpg"
        img_path.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)

        photo = Photo(
            event_id=event.id,
            filename="dl.jpg",
            original_path=str(img_path),
        )
        db_session.add(photo)
        db_session.commit()

        resp = client.post(
            "/api/download",
            json={"photo_ids": [photo.id]},
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/zip"

        buf = io.BytesIO(resp.data)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "dl.jpg" in zf.namelist()


class TestAdmin:
    """Test suite for admin endpoints."""

    def _login(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Helper to create and login admin user."""
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

    def test_stats(self, client: FlaskClient, db_session: object) -> None:
        """Stats endpoint should return counts."""
        self._login(client, db_session)
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "events" in data
        assert "photos" in data

    def test_purge_event(
        self,
        client: FlaskClient,
        db_session: object,
        tmp_path: object,
    ) -> None:
        """DELETE event should purge all data."""
        self._login(client, db_session)

        event = Event(name="Purge")
        db_session.add(event)
        db_session.commit()

        img = tmp_path / "p.jpg"
        img.write_bytes(b"data")
        photo = Photo(
            event_id=event.id,
            filename="p.jpg",
            original_path=str(img),
        )
        db_session.add(photo)
        db_session.commit()

        resp = client.delete(f"/api/admin/event/{event.id}")
        assert resp.status_code == 200

    def test_audit_logs(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Audit endpoint should return log entries."""
        self._login(client, db_session)

        log = AuditLog(action="search", match_count=5)
        db_session.add(log)
        db_session.commit()

        resp = client.get("/api/admin/audit")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1


class TestStatus:
    """Test suite for /api/status."""

    def test_status_endpoint(self, client: FlaskClient) -> None:
        """Status should return completed state."""
        resp = client.get("/api/status/123")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "completed"
