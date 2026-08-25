"""Generate face-centric thumbnails from event photos."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Create thumbnails cropped to the face area with padding."""

    def __init__(
        self,
        thumbnails_dir: Path,
        size: tuple[int, int] = (256, 256),
        padding_factor: float = 0.4,
    ) -> None:
        self.thumbnails_dir = thumbnails_dir
        self.size = size
        self.padding_factor = padding_factor
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        source_path: Path,
        face_location: tuple[int, int, int, int],
        output_filename: str,
    ) -> Path:
        """Crop to face with padding and resize."""
        top, right, bottom, left = face_location
        width = right - left
        height = bottom - top

        pad_x = int(width * self.padding_factor)
        pad_y = int(height * self.padding_factor)

        with Image.open(source_path) as img:
            img_w, img_h = img.size

            crop_left = max(0, left - pad_x)
            crop_top = max(0, top - pad_y)
            crop_right = min(img_w, right + pad_x)
            crop_bottom = min(img_h, bottom + pad_y)

            cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
            thumbnail = cropped.resize(
                self.size,
                Image.Resampling.LANCZOS,
            )

            output_path = self.thumbnails_dir / output_filename
            thumbnail.save(output_path, "JPEG", quality=85)

        logger.info("Generated thumbnail: %s", output_path)
        return output_path
