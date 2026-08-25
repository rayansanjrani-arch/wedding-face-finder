"""Unit tests for configuration validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from wedding_face_finder.config import Settings


class TestSettingsValidation:
    """Test suite for Settings validation."""

    def test_valid_settings(self, tmp_path: Path) -> None:
        """Settings should accept valid configuration."""
        base = tmp_path / "test_app"
        settings = Settings(
            secret_key="a" * 32,
            admin_password_hash=("$2b$12$validhash1234567890123456789012345678901234"),
            photos_dir=base / "photos",
            uploads_dir=base / "uploads",
            data_dir=base / "data",
        )
        assert settings.secret_key == "a" * 32
        assert settings.tolerance == 0.50
        assert settings.model == "cnn"
        assert settings.photos_dir.exists()

    def test_secret_key_too_short(self, tmp_path: Path) -> None:
        """Settings should reject secret keys shorter than 32 chars."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                secret_key="short",
                admin_password_hash=(
                    "$2b$12$validhash1234567890123456789012345678901234"
                ),
                data_dir=tmp_path / "data",
            )
        assert "at least 32 characters" in str(exc_info.value)

    def test_tolerance_out_of_range(self, tmp_path: Path) -> None:
        """Tolerance must be between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a" * 32,
                admin_password_hash=(
                    "$2b$12$validhash1234567890123456789012345678901234"
                ),
                data_dir=tmp_path / "data",
                tolerance=1.5,
            )

    def test_invalid_model(self, tmp_path: Path) -> None:
        """Only 'cnn' and 'hog' are valid models."""
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a" * 32,
                admin_password_hash=(
                    "$2b$12$validhash1234567890123456789012345678901234"
                ),
                data_dir=tmp_path / "data",
                model="invalid",  # type: ignore[arg-type]
            )

    def test_negative_retention(self, tmp_path: Path) -> None:
        """Data retention must be at least 1 day."""
        with pytest.raises(ValidationError):
            Settings(
                secret_key="a" * 32,
                admin_password_hash=(
                    "$2b$12$validhash1234567890123456789012345678901234"
                ),
                data_dir=tmp_path / "data",
                data_retention_days=0,
            )

    def test_directories_created(self, tmp_path: Path) -> None:
        """Settings should auto-create all configured directories."""
        base = tmp_path / "auto_create"
        settings = Settings(
            secret_key="a" * 32,
            admin_password_hash=("$2b$12$validhash1234567890123456789012345678901234"),
            photos_dir=base / "photos",
            uploads_dir=base / "uploads",
            thumbnails_dir=base / "thumbnails",
            data_dir=base / "data",
            logs_dir=base / "logs",
        )
        assert settings.photos_dir.is_dir()
        assert settings.uploads_dir.is_dir()
        assert settings.thumbnails_dir.is_dir()
        assert settings.data_dir.is_dir()
        assert settings.logs_dir.is_dir()

    def test_default_values(self, tmp_path: Path) -> None:
        """Default values should be sensible and secure."""
        settings = Settings(
            secret_key="a" * 32,
            admin_password_hash=("$2b$12$validhash1234567890123456789012345678901234"),
            data_dir=tmp_path / "data",
        )
        assert settings.encrypt_encodings is False
        assert settings.audit_searches is True
        assert settings.session_lifetime_minutes == 60
        assert settings.max_content_length == 5 * 1024 * 1024
        assert settings.login_rate_limit == "5 per minute"

    def test_path_from_string(self, tmp_path: Path) -> None:
        """Path fields should accept string input and convert to Path."""
        settings = Settings(
            secret_key="a" * 32,
            admin_password_hash=("$2b$12$validhash1234567890123456789012345678901234"),
            data_dir=str(tmp_path / "data"),
        )
        assert isinstance(settings.data_dir, Path)
