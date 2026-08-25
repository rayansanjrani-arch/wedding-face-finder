"""Flask application factory."""

from pathlib import Path

from flask import Flask, Response, request
from werkzeug.exceptions import HTTPException

from wedding_face_finder.config import Settings, get_settings
from wedding_face_finder.extensions import csrf, db, limiter, login_manager


def create_app(
    settings: Settings | None = None,
    database_uri: str | None = None,
) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=Path(__file__).parent / "templates",
        static_folder=Path(__file__).parent / "static",
    )

    if settings is None:
        settings = get_settings()

    _configure_app(app, settings, database_uri)
    _register_extensions(app, settings)
    _register_security_headers(app)
    _register_error_handlers(app)
    _register_blueprints(app)

    return app


def _configure_app(
    app: Flask,
    settings: Settings,
    database_uri: str | None = None,
) -> None:
    """Apply all Flask configuration from Settings."""
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{settings.data_dir / 'wedding_face_finder.db'}"
        )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = settings.flask_env == "production"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = settings.session_lifetime_minutes * 60
    app.config["ENV"] = settings.flask_env
    app.config["DEBUG"] = settings.flask_debug


def _register_extensions(app: Flask, settings: Settings) -> None:
    """Initialize Flask extensions with app context."""
    db.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from wedding_face_finder.models import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """Load user by ID for session management."""
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized() -> Response:
        """Return JSON 401 for API routes instead of redirecting."""
        if request.path.startswith("/api/"):
            return Response(
                '{"error": "Authentication required"}',
                status=401,
                mimetype="application/json",
            )
        return Response("Please log in", status=401)


def _register_security_headers(app: Flask) -> None:
    """Register security headers via after_request hook."""

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"

        if app.config.get("ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        return response


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""

    @app.errorhandler(404)
    def not_found(error: HTTPException) -> Response:
        if request.is_json or request.path.startswith("/api/"):
            return Response(
                '{"error": "Not found", "path": "' + request.path + '"}',
                status=404,
                mimetype="application/json",
            )
        return Response("Page not found", status=404)

    @app.errorhandler(429)
    def rate_limited(error: HTTPException) -> Response:
        return Response(
            '{"error": "Rate limit exceeded. Please slow down."}',
            status=429,
            mimetype="application/json",
        )

    @app.errorhandler(500)
    def server_error(error: HTTPException) -> Response:
        app.logger.error("Internal server error: %s", error)
        return Response(
            '{"error": "Internal server error. Please try again later."}',
            status=500,
            mimetype="application/json",
        )


def _register_blueprints(app: Flask) -> None:
    """Register API and view blueprints."""
    from wedding_face_finder.api.admin import admin_bp
    from wedding_face_finder.api.auth import auth_bp
    from wedding_face_finder.api.download import download_bp
    from wedding_face_finder.api.search import search_bp
    from wedding_face_finder.api.status import status_bp
    from wedding_face_finder.api.upload import upload_bp
    from wedding_face_finder.extensions import csrf
    from wedding_face_finder.views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(views_bp)

    csrf.exempt(auth_bp)
    csrf.exempt(upload_bp)
    csrf.exempt(search_bp)
    csrf.exempt(status_bp)
    csrf.exempt(download_bp)
    csrf.exempt(admin_bp)
