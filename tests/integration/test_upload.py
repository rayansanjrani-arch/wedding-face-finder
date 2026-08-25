"""Integration tests for photo upload endpoint."""

import io

from flask.testing import FlaskClient

from wedding_face_finder.models import Event, User
from wedding_face_finder.utils.security import hash_password


class TestUpload:
    """Test suite for /api/upload."""

    def _login(self, client: FlaskClient, db_session: object) -> None:
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

    def test_upload_without_auth(self, client: FlaskClient) -> None:
        """Upload without login should return 401."""
        resp = client.post(
            "/api/upload",
            data={"event_id": "1"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 401

    def test_upload_success(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Valid upload should create Photo records."""
        self._login(client, db_session)

        event = Event(name="Test Event")
        db_session.add(event)
        db_session.commit()

        data = {
            "event_id": str(event.id),
            "photos": (
                io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100),
                "test.jpg",
            ),
        }
        resp = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        assert b"Uploaded" in resp.data

    def test_upload_invalid_file_type(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Non-image files should be rejected."""
        self._login(client, db_session)

        event = Event(name="Test Event")
        db_session.add(event)
        db_session.commit()

        data = {
            "event_id": str(event.id),
            "photos": (io.BytesIO(b"not an image"), "test.txt"),
        }
        resp = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_upload_event_not_found(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Upload to non-existent event should return 404."""
        self._login(client, db_session)

        data = {
            "event_id": "999",
            "photos": (
                io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100),
                "test.jpg",
            ),
        }
        resp = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 404

    def test_upload_file_too_large(
        self,
        client: FlaskClient,
        db_session: object,
    ) -> None:
        """Files exceeding max size should be rejected with 413."""
        self._login(client, db_session)

        event = Event(name="Test Event")
        db_session.add(event)
        db_session.commit()

        data = {
            "event_id": str(event.id),
            "photos": (
                io.BytesIO(b"\xff\xd8\xff" + b"\x00" * (6 * 1024 * 1024)),
                "huge.jpg",
            ),
        }
        resp = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 413
