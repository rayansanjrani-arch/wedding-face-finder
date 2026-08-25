"""SQLAlchemy ORM models using Flask-SQLAlchemy 3.x."""

from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wedding_face_finder.extensions import Base


class Event(Base):
    """An event (wedding, party, conference) with a photo album."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    photos: Mapped[list["Photo"]] = relationship(
        "Photo", back_populates="event", cascade="all, delete-orphan", lazy="select"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="event", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name={self.name!r})>"


class Photo(Base):
    """A photo file belonging to an event."""

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    original_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    event: Mapped["Event"] = relationship("Event", back_populates="photos")
    faces: Mapped[list["Face"]] = relationship(
        "Face", back_populates="photo", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, filename={self.filename!r})>"


class Face(Base):
    """A detected face within a photo, stored as a 128-dim encoding vector."""

    __tablename__ = "faces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    photo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    face_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Index of this face within the photo (0-based)"
    )
    encoding: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="128-dim face encoding (float32 array)"
    )
    location_top: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location_right: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location_bottom: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location_left: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if encoding was encrypted before storage",
    )

    photo: Mapped["Photo"] = relationship("Photo", back_populates="faces")

    __table_args__ = (
        UniqueConstraint("photo_id", "face_index", name="uix_photo_face_index"),
    )

    def __repr__(self) -> str:
        return (
            f"<Face(id={self.id}, photo_id={self.photo_id}, "
            f"index={self.face_index})>"
        )


class User(Base, UserMixin):
    """Admin user for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r})>"


class AuditLog(Base):
    """Immutable audit trail for compliance and security monitoring."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="e.g., 'search', 'upload', 'login', 'purge'",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    match_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    event: Mapped[Optional["Event"]] = relationship(
        "Event", back_populates="audit_logs"
    )

    __table_args__ = (
        Index("ix_audit_logs_action_created", "action", "created_at"),
        Index("ix_audit_logs_ip_created", "ip_address", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action!r}, "
            f"event_id={self.event_id})>"
        )
