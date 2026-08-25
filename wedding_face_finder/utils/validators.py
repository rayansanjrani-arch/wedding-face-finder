"""Input validation: magic bytes, MIME types, file size, base64."""

import base64
from pathlib import Path

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
GIF_MAGIC = (b"GIF87a", b"GIF89a")


class ValidationError(Exception):
    """Raised when input fails validation."""


def validate_magic_bytes(data: bytes) -> str:
    """Detect image format from magic bytes."""
    if data.startswith(JPEG_MAGIC):
        return "image/jpeg"
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(GIF_MAGIC):
        return "image/gif"
    raise ValidationError("Invalid image format: magic bytes do not match JPEG/PNG/GIF")


def validate_file_size(data: bytes, max_size: int = 5 * 1024 * 1024) -> None:
    """Reject files exceeding max_size."""
    if len(data) > max_size:
        raise ValidationError(f"File too large: {len(data)} bytes (max {max_size})")


def validate_base64_image(b64_string: str) -> bytes:
    """Decode and validate base64 image data."""
    try:
        data = base64.b64decode(b64_string)
    except Exception as exc:
        raise ValidationError("Invalid base64 encoding") from exc
    validate_file_size(data)
    validate_magic_bytes(data)
    return data


def validate_filename(filename: str) -> str:
    """Sanitize and validate uploaded filename."""
    safe = Path(filename).name
    if not safe or safe.startswith("."):
        raise ValidationError("Invalid filename")
    ext = Path(safe).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif"}:
        raise ValidationError(f"Disallowed file extension: {ext}")
    return safe
