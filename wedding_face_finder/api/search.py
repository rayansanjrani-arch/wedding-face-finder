"""Selfie search blueprint."""

import json
import tempfile
import uuid
from pathlib import Path

import numpy as np
from flask import Blueprint, Response, request

from wedding_face_finder.config import get_settings
from wedding_face_finder.extensions import db, limiter
from wedding_face_finder.models import Event, Face, Photo
from wedding_face_finder.services.face_matcher import FaceMatcher
from wedding_face_finder.services.face_processor import FaceProcessor
from wedding_face_finder.services.security_service import AuditService
from wedding_face_finder.utils.validators import ValidationError, validate_base64_image

search_bp = Blueprint("search", __name__, url_prefix="/api")


@search_bp.route("/search", methods=["POST"])
@limiter.limit("10 per minute")
def search() -> Response:
    """Find matching photos from a selfie upload."""
    settings = get_settings()
    data = request.get_json(silent=True) or {}

    event_id = data.get("event_id")
    b64_image = data.get("image", "")

    if not event_id or not b64_image:
        return Response(
            '{"error": "event_id and image required"}',
            status=400,
            mimetype="application/json",
        )

    event = db.session.get(Event, event_id)
    if event is None:
        return Response(
            '{"error": "Event not found"}',
            status=404,
            mimetype="application/json",
        )

    try:
        img_data = validate_base64_image(b64_image)
    except ValidationError as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=400,
            mimetype="application/json",
        )

    tmp_path = Path(tempfile.gettempdir()) / f"search_{uuid.uuid4().hex}.jpg"
    tmp_path.write_bytes(img_data)

    try:
        processor = FaceProcessor(settings)
        results = processor.process_image(tmp_path)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Face processing failed: {e}"}),
            status=400,
            mimetype="application/json",
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if not results:
        return Response(
            '{"matches": []}',
            status=200,
            mimetype="application/json",
        )

    query_encoding = results[0].encoding

    faces = db.session.query(Face).join(Photo).filter(Photo.event_id == event_id).all()

    candidates: list[tuple[int, int, np.ndarray]] = []
    for face in faces:
        arr = np.frombuffer(face.encoding, dtype=np.float32).copy()
        candidates.append((face.photo_id, face.face_index, arr))

    matcher = FaceMatcher(settings)
    matches = matcher.find_matches(query_encoding, candidates)

    match_list: list[dict] = []
    for m in matches:
        photo = db.session.get(Photo, m.photo_id)
        match_list.append(
            {
                "photo_id": m.photo_id,
                "face_index": m.face_index,
                "confidence": round(m.confidence, 4),
                "distance": round(m.distance, 4),
                "thumbnail_path": photo.thumbnail_path if photo else None,
            }
        )

    audit = AuditService(db.session, enabled=settings.audit_searches)
    audit.log_search(
        event_id=event_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        match_count=len(match_list),
        details="Guest selfie search",
    )

    return Response(
        json.dumps({"matches": match_list}),
        status=200,
        mimetype="application/json",
    )
