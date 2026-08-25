"""Pydantic Settings with validation and auto-directory creation."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator, Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore[no-redef]


class Settings(BaseSettings):
    """Application settings with security and privacy defaults."""

    # Required secrets
    secret_key: str = Field(..., min_length=32)
    admin_password_hash: str

    # Directory paths (auto-created on instantiation)
    photos_dir: Path = Path("photos")
    uploads_dir: Path = Path("uploads")
    thumbnails_dir: Path = Path("thumbnails")
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")

    # Flask
    flask_env: Literal["development", "testing", "production"] = "production"
    flask_debug: bool = False

    # Face engine
    model: Literal["cnn", "hog"] = "cnn"
    tolerance: float = Field(default=0.50, ge=0.0, le=1.0)
    blur_threshold: float = 100.0

    # Security & privacy
    encrypt_encodings: bool = False
    encryption_key: str | None = None
    audit_searches: bool = True
    data_retention_days: int = Field(default=30, ge=1)
    session_lifetime_minutes: int = 60
    login_rate_limit: str = "5 per minute"

    # Upload & rate limits
    max_content_length: int = 5 * 1024 * 1024
    rate_limit_storage: str = "memory"

    @field_validator("secret_key")
    @classmethod
    def _validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return v

    @field_validator(
        "photos_dir",
        "uploads_dir",
        "thumbnails_dir",
        "data_dir",
        "logs_dir",
        mode="before",
    )
    @classmethod
    def _coerce_path(cls, v: str | Path) -> Path:
        return Path(v)

    @field_validator(
        "photos_dir",
        "uploads_dir",
        "thumbnails_dir",
        "data_dir",
        "logs_dir",
    )
    @classmethod
    def _create_directory(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """Load settings from environment and .env file."""
    return Settings()
