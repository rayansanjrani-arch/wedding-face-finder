"""Admin dashboard and management blueprint."""

import json

from flask import Blueprint, Response
from flask_login import login_required

from wedding_face_finder.config import get_settings
from wedding_face_finder.extensions import db
from wedding_face_finder.models import AuditLog, Event, Photo
from wedding_face_finder.services.security_service import PurgeService

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/stats", methods=["GET"])
@login_required
def stats() -> Response:
    """Return event and photo counts."""
    event_count = db.session.query(Event).count()
    photo_count = db.session.query(Photo).count()
    return Response(
        json.dumps({"events": event_count, "photos": photo_count}),
        status=200,
        mimetype="application/json",
    )


@admin_bp.route("/event/<int:event_id>", methods=["DELETE"])
@login_required
def delete_event(event_id: int) -> Response:
    """Purge an event and all associated data."""
    settings = get_settings()
    service = PurgeService(settings, db.session)
    try:
        service.purge_event(event_id)
        return Response(
            '{"message": "Event purged"}',
            status=200,
            mimetype="application/json",
        )
    except ValueError:
        return Response(
            '{"error": "Event not found"}',
            status=404,
            mimetype="application/json",
        )


@admin_bp.route("/audit", methods=["GET"])
@login_required
def audit_logs() -> Response:
    """Return recent audit log entries."""
    logs = (
        db.session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    )
    data = [
        {
            "id": log.id,
            "action": log.action,
            "event_id": log.event_id,
            "ip_address": log.ip_address,
            "match_count": log.match_count,
            "created_at": (log.created_at.isoformat() if log.created_at else None),
        }
        for log in logs
    ]
    return Response(
        json.dumps(data),
        status=200,
        mimetype="application/json",
    )
