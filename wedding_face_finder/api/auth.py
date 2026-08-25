"""Authentication blueprint: login, logout, session management."""

from flask import Blueprint, Response, request
from flask_login import login_required, login_user, logout_user

from wedding_face_finder.extensions import db, limiter
from wedding_face_finder.models import User
from wedding_face_finder.utils.security import verify_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api/admin")


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login() -> Response:
    """Authenticate admin and create session."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return Response(
            '{"error": "Username and password required"}',
            status=400,
            mimetype="application/json",
        )

    user = db.session.query(User).filter_by(username=username).first()
    if user is None or not verify_password(password, user.password_hash):
        return Response(
            '{"error": "Invalid credentials"}',
            status=401,
            mimetype="application/json",
        )

    if not user.is_active:
        return Response(
            '{"error": "Account disabled"}',
            status=403,
            mimetype="application/json",
        )

    login_user(user)
    return Response(
        '{"message": "Login successful"}',
        status=200,
        mimetype="application/json",
    )


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout() -> Response:
    """Clear admin session."""
    logout_user()
    return Response(
        '{"message": "Logout successful"}',
        status=200,
        mimetype="application/json",
    )
