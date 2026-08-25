"""Security services: encryption, audit logging, data purging."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet

from wedding_face_finder.config import Settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from wedding_face_finder.models import AuditLog

logger = logging.getLogger(__name__)


class EncryptionService:
    """Optional Fernet encryption for face encodings at rest."""

    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.encrypt_encodings
        if self.enabled:
            if not settings.encryption_key:
                raise RuntimeError("encrypt_encodings=True but ENCRYPTION_KEY not set")
            self._fernet = Fernet(settings.encryption_key)
        else:
            self._fernet = None

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt bytes if enabled, else pass through."""
        if not self.enabled or self._fernet is None:
            return data
        return self._fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt bytes if enabled, else pass through."""
        if not self.enabled or self._fernet is None:
            return data
        return self._fernet.decrypt(data)


class AuditService:
    """Write structured audit logs to database."""

    def __init__(self, db_session: Session, enabled: bool = True) -> None:
        self.db_session = db_session
        self.enabled = enabled

    def log_search(
        self,
        event_id: int | None,
        ip_address: str | None,
        user_agent: str | None,
        match_count: int,
        details: str = "",
    ) -> AuditLog | None:
        """Log a search action."""
        if not self.enabled:
            return None

        from wedding_face_finder.models import AuditLog

        log = AuditLog(
            event_id=event_id,
            action="search",
            ip_address=ip_address,
            user_agent=user_agent,
            match_count=match_count,
            details=details,
        )
        self.db_session.add(log)
        self.db_session.commit()
        logger.info(
            "Audit: search event=%s matches=%s",
            event_id,
            match_count,
        )
        return log


class PurgeService:
    """Auto-purge old uploads and scrub events."""

    def __init__(
        self,
        settings: Settings,
        db_session: Session,
    ) -> None:
        self.settings = settings
        self.db_session = db_session

    def purge_old_uploads(self) -> int:
        """Remove files in uploads/ older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=self.settings.data_retention_days
        )
        count = 0

        for path in self.settings.uploads_dir.iterdir():
            if not path.is_file():
                continue
            mtime = datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.utc,
            )
            if mtime < cutoff:
                path.unlink()
                count += 1
                logger.info("Purged upload: %s", path)

        return count

    def purge_event(self, event_id: int) -> None:
        """Scrub all data for a specific event."""
        from wedding_face_finder.models import Event

        event = self.db_session.get(Event, event_id)
        if event is None:
            raise ValueError(f"Event {event_id} not found")

        for photo in event.photos:
            for attr in ("original_path", "thumbnail_path"):
                p = getattr(photo, attr, None)
                if p:
                    fp = Path(p)
                    if fp.exists():
                        fp.unlink()
                        logger.info("Deleted file: %s", fp)

        self.db_session.delete(event)
        self.db_session.commit()
        logger.info("Purged event %s", event_id)
