"""Integration tests for search endpoint."""

import base64

import numpy as np
from flask.testing import FlaskClient

from wedding_face_finder.models import Event, Face, Photo
from wedding_face_finder.services.face_processor import FaceProcessor, FaceResult


class TestSearch:
    """Test suite for /api/search."""

    def test_search_missing_fields(self, client: FlaskClient) -> None:
        """Missing event_id or image should return 400."""
        resp = client.post("/api/search", json={})
        assert resp.status_code == 400

    def test_search_event_not_found(self, client: FlaskClient) -> None:
        """Search for non-existent event should return 404."""
        img_b64 = base64.b64encode(b"\xff\xd8\xff" + b"\x00" * 100).decode()
        resp = client.post(
            "/api/search",
            json={"event_id": 999, "image": img_b64},
        )
        assert resp.status_code == 404

    def test_search_invalid_image(
        self, client: FlaskClient, db_session: object
    ) -> None:
        """Invalid base64 or bad magic bytes should return 400."""
        event = Event(name="Invalid")
        db_session.add(event)
        db_session.commit()

        resp = client.post(
            "/api/search",
            json={"event_id": event.id, "image": "not-valid-base64!!!"},
        )
        assert resp.status_code == 400

    def test_search_success(
        self,
        client: FlaskClient,
        db_session: object,
        monkeypatch: object,
    ) -> None:
        """Valid search should return matches."""
        event = Event(name="Search Event")
        db_session.add(event)
        db_session.commit()

        photo = Photo(
            event_id=event.id,
            filename="s.jpg",
            original_path="/tmp/s.jpg",
        )
        db_session.add(photo)
        db_session.commit()

        enc = np.zeros(128, dtype=np.float32)
        face = Face(
            photo_id=photo.id,
            face_index=0,
            encoding=enc.tobytes(),
        )
        db_session.add(face)
        db_session.commit()

        def mock_process(self, path):  # type: ignore[no-untyped-def]
            return [
                FaceResult(
                    encoding=enc,
                    location=(0, 0, 0, 0),
                    confidence=1.0,
                    face_index=0,
                )
            ]

        monkeypatch.setattr(FaceProcessor, "process_image", mock_process)

        img_b64 = base64.b64encode(b"\xff\xd8\xff" + b"\x00" * 100).decode()
        resp = client.post(
            "/api/search",
            json={"event_id": event.id, "image": img_b64},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "matches" in data
        assert len(data["matches"]) >= 1
        assert data["matches"][0]["photo_id"] == photo.id
