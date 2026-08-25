"""Photo download blueprint."""

import io
import zipfile
from pathlib import Path

from flask import Blueprint, Response, request
from flask_login import login_required

from wedding_face_finder.extensions import db
from wedding_face_finder.models import Photo

download_bp = Blueprint("download", __name__, url_prefix="/api")


@download_bp.route("/download", methods=["POST"])
@login_required
def download_photos() -> Response:
    """Generate ZIP of selected photos."""
    data = request.get_json(silent=True) or {}
    photo_ids = data.get("photo_ids", [])

    if not photo_ids:
        return Response(
            '{"error": "photo_ids required"}',
            status=400,
            mimetype="application/json",
        )

    photos = db.session.query(Photo).filter(Photo.id.in_(photo_ids)).all()
    if not photos:
        return Response(
            '{"error": "No photos found"}',
            status=404,
            mimetype="application/json",
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            p = Path(photo.original_path)
            if p.exists():
                zf.write(p, arcname=p.name)

    buf.seek(0)
    return Response(
        buf.getvalue(),
        status=200,
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=photos.zip"},
    )
