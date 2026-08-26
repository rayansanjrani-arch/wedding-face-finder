"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Flask
    secret_key: str = Field(..., min_length=32)
    flask_env: Literal["development", "production", "testing"] = Field(
        default="development"
    )
    flask_debug: bool = Field(default=False)
    session_lifetime_minutes: int = Field(default=60)

    # Database
    database_url: str = Field(default="sqlite:///wedding_face_finder.db")

    # File storage
    upload_folder: str = Field(default="uploads")
    thumbnail_folder: str = Field(default="thumbnails")
    photos_dir: Path = Field(default=Path("photos"))
    uploads_dir: Path = Field(default=Path("uploads"))
    thumbnails_dir: Path = Field(default=Path("thumbnails"))
    data_dir: Path = Field(default=Path("data"))
    logs_dir: Path = Field(default=Path("logs"))
    max_upload_size_mb: int = Field(default=5)
    max_content_length: int = Field(default=5 * 1024 * 1024)

    # Face recognition
    tolerance: float = Field(default=0.5)
    model: Literal["hog", "cnn"] = Field(default="cnn")
    blur_threshold: float = Field(default=100.0)
    encrypt_encodings: bool = Field(default=False)

    # Security
    admin_password_hash: str = Field(...)
    enable_audit_logging: bool = Field(default=True)
    audit_searches: bool = Field(default=True)
    encryption_key: str | None = Field(default=None)
    rate_limit_storage: str = Field(default="memory")
    login_rate_limit: str = Field(default="5 per minute")

    # Data retention
    data_retention_days: int = Field(default=30, ge=1)

    # Pagination
    default_page_size: int = Field(default=20)
    max_page_size: int = Field(default=100)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("tolerance")
    @classmethod
    def _validate_tolerance(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Tolerance must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def create_directories(self) -> "Settings":
        """Ensure all configured directories exist."""
        for attr in (
            "photos_dir",
            "uploads_dir",
            "thumbnails_dir",
            "data_dir",
            "logs_dir",
        ):
            path = getattr(self, attr)
            if path is not None:
                path.mkdir(parents=True, exist_ok=True)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
