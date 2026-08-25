"""Image processing helpers: base64, compression, OpenCV."""

import base64
import io
from pathlib import Path

from PIL import Image


def decode_base64_image(b64_string: str) -> bytes:
    """Decode base64 string to raw bytes."""
    return base64.b64decode(b64_string)


def encode_base64_image(data: bytes) -> str:
    """Encode raw bytes to base64 string."""
    return base64.b64encode(data).decode("ascii")


def compress_image(
    data: bytes,
    max_size: tuple[int, int] = (1024, 1024),
    quality: int = 85,
) -> bytes:
    """Compress image to target dimensions and quality."""
    buf = io.BytesIO(data)
    with Image.open(buf) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        out = io.BytesIO()
        fmt = img.format or "JPEG"
        img.save(out, format=fmt, quality=quality)
        return out.getvalue()


def save_upload(data: bytes, dest_dir: Path, filename: str) -> Path:
    """Save upload data to destination directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    dest_path.write_bytes(data)
    return dest_path
