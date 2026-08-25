"""HTML view routes for the frontend."""

from flask import Blueprint, render_template, send_from_directory
from flask_login import login_required

from wedding_face_finder.config import get_settings
from wedding_face_finder.extensions import db
from wedding_face_finder.models import Photo

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index() -> str:
    """Landing page."""
    return render_template("index.html")


@views_bp.route("/upload")
def upload_page() -> str:
    """Selfie upload page."""
    return render_template("upload.html")


@views_bp.route("/results")
def results_page() -> str:
    """Search results page."""
    return render_template("results.html")


@views_bp.route("/admin/login")
def admin_login() -> str:
    """Admin login page."""
    return render_template("admin/login.html")


@views_bp.route("/admin/dashboard")
@login_required
def admin_dashboard() -> str:
    """Admin dashboard."""
    return render_template("admin/dashboard.html")


@views_bp.route("/api/photos/<int:photo_id>")
def serve_photo(photo_id: int) -> tuple:
    """Serve original photo file."""
    photo = db.session.get(Photo, photo_id)
    if photo is None:
        return "Not found", 404
    settings = get_settings()
    return send_from_directory(
        settings.photos_dir,
        photo.filename,
    )


@views_bp.route("/health")
def health() -> tuple:
    return {"status": "ok"}, 200
