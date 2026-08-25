"""Unit tests for database layer."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from wedding_face_finder.models import (
    AuditLog,
    Event,
    Face,
    Photo,
    User,
)


class TestEventModel:
    """Test suite for Event ORM model."""

    def test_create_event(self, db_session: Session) -> None:
        """Should create an event with default values."""
        event = Event(name="Test Wedding", description="A lovely ceremony")
        db_session.add(event)
        db_session.commit()

        assert event.id is not None
        assert event.name == "Test Wedding"
        assert event.is_active is True
        assert event.created_at is not None

    def test_event_photos_relationship(self, db_session: Session) -> None:
        """Should link photos to an event via relationship."""
        event = Event(name="Photo Test")
        db_session.add(event)
        db_session.commit()

        photo = Photo(
            event_id=event.id,
            filename="test.jpg",
            original_path="/photos/test.jpg",
        )
        db_session.add(photo)
        db_session.commit()

        assert len(event.photos) == 1
        assert event.photos[0].filename == "test.jpg"

    def test_event_cascade_delete(self, db_session: Session) -> None:
        """Deleting an event should delete its photos and faces."""
        event = Event(name="Cascade Test")
        db_session.add(event)
        db_session.commit()

        photo = Photo(
            event_id=event.id,
            filename="cascade.jpg",
            original_path="/photos/cascade.jpg",
        )
        db_session.add(photo)
        db_session.commit()

        face = Face(
            photo_id=photo.id,
            face_index=0,
            encoding=b"\x00" * 512,
        )
        db_session.add(face)
        db_session.commit()

        db_session.delete(event)
        db_session.commit()

        assert db_session.query(Photo).filter_by(id=photo.id).first() is None
        assert db_session.query(Face).filter_by(id=face.id).first() is None


class TestPhotoModel:
    """Test suite for Photo ORM model."""

    def test_photo_faces_relationship(self, db_session: Session) -> None:
        """Should link faces to a photo."""
        event = Event(name="Face Test")
        db_session.add(event)
        db_session.commit()

        photo = Photo(
            event_id=event.id,
            filename="faces.jpg",
            original_path="/photos/faces.jpg",
        )
        db_session.add(photo)
        db_session.commit()

        face1 = Face(photo_id=photo.id, face_index=0, encoding=b"\x00" * 512)
        face2 = Face(photo_id=photo.id, face_index=1, encoding=b"\x01" * 512)
        db_session.add_all([face1, face2])
        db_session.commit()

        assert len(photo.faces) == 2
        assert photo.faces[0].face_index == 0
        assert photo.faces[1].face_index == 1

    def test_unique_face_index_per_photo(self, db_session: Session) -> None:
        """Should enforce unique (photo_id, face_index) constraint."""
        event = Event(name="Unique Test")
        db_session.add(event)
        db_session.commit()

        photo = Photo(
            event_id=event.id,
            filename="unique.jpg",
            original_path="/photos/unique.jpg",
        )
        db_session.add(photo)
        db_session.commit()

        face1 = Face(photo_id=photo.id, face_index=0, encoding=b"\x00" * 512)
        db_session.add(face1)
        db_session.commit()

        face2 = Face(photo_id=photo.id, face_index=0, encoding=b"\x01" * 512)
        db_session.add(face2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestUserModel:
    """Test suite for User ORM model."""

    def test_create_user(self, db_session: Session) -> None:
        """Should create a user with required fields."""
        user = User(
            username="testadmin",
            password_hash=("$2b$12$testhash1234567890123456789012345678901234"),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testadmin"
        assert user.is_active is True
        assert user.created_at is not None

    def test_unique_username(self, db_session: Session) -> None:
        """Should enforce unique username constraint."""
        user1 = User(
            username="uniqueuser",
            password_hash="$2b$12$hash1",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            username="uniqueuser",
            password_hash="$2b$12$hash2",
        )
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestAuditLogModel:
    """Test suite for AuditLog ORM model."""

    def test_create_audit_log(self, db_session: Session) -> None:
        """Should create an audit log entry."""
        event = Event(name="Audit Test")
        db_session.add(event)
        db_session.commit()

        log = AuditLog(
            event_id=event.id,
            action="search",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            details="Guest searched for their photos",
            match_count=12,
        )
        db_session.add(log)
        db_session.commit()

        assert log.id is not None
        assert log.action == "search"
        assert log.match_count == 12
        assert log.created_at is not None

    def test_audit_log_without_event(self, db_session: Session) -> None:
        """Should allow audit logs without event (system-level actions)."""
        log = AuditLog(
            action="login",
            ip_address="10.0.0.1",
            details="Admin login attempt",
        )
        db_session.add(log)
        db_session.commit()

        assert log.event_id is None
        assert log.action == "login"
