"""Unit tests for thumbnail generation."""

from pathlib import Path

from PIL import Image

from wedding_face_finder.services.thumbnail_generator import (
    ThumbnailGenerator,
)


class TestThumbnailGenerator:
    """Test suite for face-centric thumbnail creation."""

    def test_generate_thumbnail(
        self,
        tmp_path: Path,
        test_settings: object,
    ) -> None:
        """Should crop to face and resize to thumbnail dimensions."""
        source = tmp_path / "source.jpg"
        img = Image.new("RGB", (500, 500), color="red")
        img.save(source, "JPEG")

        gen = ThumbnailGenerator(
            thumbnails_dir=test_settings.thumbnails_dir,
            size=(256, 256),
        )
        face_loc = (100, 200, 200, 100)
        output = gen.generate(source, face_loc, "thumb_001.jpg")

        assert output.exists()
        assert output.name == "thumb_001.jpg"
        with Image.open(output) as thumb:
            assert thumb.size == (256, 256)

    def test_padding_clamped_to_edges(
        self,
        tmp_path: Path,
        test_settings: object,
    ) -> None:
        """Should not crop beyond image boundaries."""
        source = tmp_path / "small.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(source, "JPEG")

        gen = ThumbnailGenerator(
            thumbnails_dir=test_settings.thumbnails_dir,
            size=(128, 128),
            padding_factor=1.0,
        )
        face_loc = (40, 60, 60, 40)
        output = gen.generate(source, face_loc, "thumb_002.jpg")

        assert output.exists()
        with Image.open(output) as thumb:
            assert thumb.size == (128, 128)
