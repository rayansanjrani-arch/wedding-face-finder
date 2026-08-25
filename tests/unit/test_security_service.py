"""Unit tests for security services."""

import os
import time
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from wedding_face_finder.config import Settings
from wedding_face_finder.models import Event, Photo
from wedding_face_finder.services.security_service import (
    AuditService,
    EncryptionService,
    PurgeService,
)


class TestEncryptionService:
    """Test suite for encoding encryption."""

    def test_disabled_passthrough(
        self,
        test_settings: Settings,
    ) -> None:
        """When disabled, encrypt/decrypt returns data unchanged."""
        service = EncryptionService(test_settings)
        data = b"face_encoding_data"
        assert service.encrypt(data) == data
        assert service.decrypt(data) == data

    def test_enabled_roundtrip(self, tmp_path: Path) -> None:
        """Encrypt then decrypt recovers original data."""
        key = Fernet.generate_key().decode()
        settings = Settings(
            secret_key="a" * 32,
            admin_password_hash=("$2b$12$validhash1234567890123456789012345678901234"),
            data_dir=tmp_path / "data",
            encrypt_encodings=True,
            encryption_key=key,
        )
        service = EncryptionService(settings)
        data = b"secret_biometric_data"
        encrypted = service.encrypt(data)
        assert encrypted != data
        decrypted = service.decrypt(encrypted)
        assert decrypted == data

    def test_enabled_missing_key(self, tmp_path: Path) -> None:
        """Should raise RuntimeError if key missing."""
        settings = Settings(
            secret_key="a" * 32,
            admin_password_hash=("$2b$12$validhash1234567890123456789012345678901234"),
            data_dir=tmp_path / "data",
            encrypt_encodings=True,
            encryption_key=None,
        )
        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
            EncryptionService(settings)


class TestAuditService:
    """Test suite for audit logging."""

    def test_log_search_when_enabled(
        self,
        db_session: object,
    ) -> None:
        """Should create an AuditLog row when enabled."""
        service = AuditService(db_session, enabled=True)
        event = Event(name="Audit Event")
        db_session.add(event)
        db_session.commit()

        log = service.log_search(
            event_id=event.id,
            ip_address="192.168.1.1",
            user_agent="TestAgent",
            match_count=5,
            details="test search",
        )
        assert log is not None
        assert log.action == "search"
        assert log.match_count == 5

    def test_log_search_when_disabled(
        self,
        db_session: object,
    ) -> None:
        """Should return None when auditing is disabled."""
        service = AuditService(db_session, enabled=False)
        log = service.log_search(
            event_id=None,
            ip_address=None,
            user_agent=None,
            match_count=0,
        )
        assert log is None


class TestPurgeService:
    """Test suite for data purging."""

    def test_purge_old_uploads(
        self,
        db_session: object,
        test_settings: Settings,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should delete files older than retention period."""
        uploads = tmp_path / "uploads"
        uploads.mkdir()
        monkeypatch.setattr(test_settings, "uploads_dir", uploads)

        old_file = uploads / "old.jpg"
        old_file.write_text("old")
        old_time = time.time() - ((test_settings.data_retention_days + 1) * 86400)
        os.utime(old_file, (old_time, old_time))

        new_file = uploads / "new.jpg"
        new_file.write_text("new")

        service = PurgeService(test_settings, db_session)
        count = service.purge_old_uploads()

        assert count == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_purge_event(
        self,
        db_session: object,
        test_settings: Settings,
        tmp_path: Path,
    ) -> None:
        """Should delete event, DB rows, and associated files."""
        event = Event(name="Purge Event")
        db_session.add(event)
        db_session.commit()

        photo_file = tmp_path / "photo.jpg"
        photo_file.write_text("photo")
        thumb_file = tmp_path / "thumb.jpg"
        thumb_file.write_text("thumb")

        photo = Photo(
            event_id=event.id,
            filename="photo.jpg",
            original_path=str(photo_file),
            thumbnail_path=str(thumb_file),
        )
        db_session.add(photo)
        db_session.commit()

        service = PurgeService(test_settings, db_session)
        service.purge_event(event.id)

        assert db_session.get(Event, event.id) is None
        assert not photo_file.exists()
        assert not thumb_file.exists()
