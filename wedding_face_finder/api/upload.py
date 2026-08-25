"""Photo upload blueprint for event albums."""

import uuid
from pathlib import Path

from flask import Blueprint, Response, request
from flask_login import login_required
from werkzeug.utils import secure_filename

from wedding_face_finder.config import get_settings
from wedding_face_finder.extensions import db
from wedding_face_finder.models import Event, Photo
from wedding_face_finder.utils.validators import (
    ValidationError,
    validate_file_size,
    validate_magic_bytes,
)

upload_bp = Blueprint("upload", __name__, url_prefix="/api")


@upload_bp.route("/upload", methods=["POST"])
@login_required
def upload_photos() -> Response:
    """Batch upload photos for an event."""
    settings = get_settings()

    event_id = request.form.get("event_id", type=int)
    if not event_id:
        return Response(
            '{"error": "event_id required"}',
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

    files = request.files.getlist("photos")
    if not files or all(not f.filename for f in files):
        return Response(
            '{"error": "No photos provided"}',
            status=400,
            mimetype="application/json",
        )

    created_ids: list[int] = []
    for file_storage in files:
        if not file_storage.filename:
            continue

        data = file_storage.read()
        try:
            validate_file_size(data, max_size=settings.max_content_length)
            validate_magic_bytes(data)
        except ValidationError as e:
            return Response(
                f'{{"error": "{e}"}}',
                status=400,
                mimetype="application/json",
            )

        ext = Path(secure_filename(file_storage.filename)).suffix
        if not ext:
            ext = ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = settings.photos_dir / filename
        dest.write_bytes(data)

        photo = Photo(
            event_id=event_id,
            filename=filename,
            original_path=str(dest),
            file_size_bytes=len(data),
        )
        db.session.add(photo)
        db.session.flush()
        created_ids.append(photo.id)

    db.session.commit()
    return Response(
        (
            f'{{"message": "Uploaded {len(created_ids)} photos", '
            f'"photo_ids": {created_ids}}}'
        ),
        status=201,
        mimetype="application/json",
    )
