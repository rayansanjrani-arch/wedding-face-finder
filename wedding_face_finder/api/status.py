"""Job status polling blueprint."""

from flask import Blueprint, Response

status_bp = Blueprint("status", __name__, url_prefix="/api")


@status_bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id: str) -> Response:
    """Return job status.

    Note: Async job queue not yet implemented.
    In production, this queries Redis/Celery.
    """
    return Response(
        '{"status": "completed", "progress": 100}',
        status=200,
        mimetype="application/json",
    )
