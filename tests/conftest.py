"""Pytest fixtures shared across all test modules."""

import os
import sys
from pathlib import Path
from typing import Generator

# Set required env vars before any app imports so get_settings() works in CI
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "ADMIN_PASSWORD_HASH",
    "$2b$04$3EKbDPV3JDkQT2WSb6Rm4ejxR3mYu9YOJiX/AY2QlQXNgS6QY5uOO",
)

import pytest  # noqa: E402
from flask import Flask  # noqa: E402
from flask.testing import FlaskClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from tests.mocks import face_recognition as _fr_mock  # noqa: E402

sys.modules["face_recognition"] = _fr_mock

from wedding_face_finder.app import create_app  # noqa: E402
from wedding_face_finder.config import Settings  # noqa: E402
from wedding_face_finder.extensions import db  # noqa: E402
from wedding_face_finder.models import User  # noqa: E402


@pytest.fixture(scope="session")
def face_recognition_mock() -> object:
    """Return the deterministic mock face_recognition module."""
    return _fr_mock


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    """Return test-specific settings with isolated directories."""
    base = tmp_path_factory.mktemp("wff_test")
    return Settings(
        secret_key="test-secret-key-that-is-32-chars-long-for-testing-only",
        admin_password_hash=(
            "$2b$04$3EKbDPV3JDkQT2WSb6Rm4ejxR3mYu9YOJiX/AY2QlQXNgS6QY5uOO"
        ),
        photos_dir=base / "photos",
        uploads_dir=base / "uploads",
        thumbnails_dir=base / "thumbnails",
        data_dir=base / "data",
        logs_dir=base / "logs",
        flask_env="testing",
        flask_debug=False,
        encrypt_encodings=False,
        audit_searches=False,
        rate_limit_storage="memory",
        blur_threshold=100.0,
        encryption_key=None,
    )


@pytest.fixture(scope="function")
def app(test_settings: Settings, tmp_path: Path) -> Generator[Flask, None, None]:
    """Create a fresh Flask app with file-based SQLite for each test."""
    db_file = tmp_path / "test.db"
    app = create_app(
        settings=test_settings,
        database_uri=f"sqlite:///{db_file}",
    )
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Return a test HTTP client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app: Flask) -> Generator[Session, None, None]:
    """Provide the Flask-SQLAlchemy session for database operations."""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture(scope="function")
def admin_user(db_session: Session, test_settings: Settings) -> User:
    """Create and return an admin user in the test database."""
    user = User(
        username="admin",
        password_hash=test_settings.admin_password_hash,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
