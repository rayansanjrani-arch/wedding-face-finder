"""Unit tests for face processing pipeline."""

from pathlib import Path

import numpy as np
import pytest

from wedding_face_finder.config import Settings
from wedding_face_finder.services.face_processor import (
    BlurError,
    FaceProcessor,
    FaceResult,
)


@pytest.fixture
def processor(
    test_settings: Settings,
    face_recognition_mock: object,
) -> FaceProcessor:
    """Return a FaceProcessor using the mock module."""
    return FaceProcessor(
        settings=test_settings,
        face_recognition_module=face_recognition_mock,
    )


class TestFaceProcessor:
    """Test suite for face detection and encoding extraction."""

    def test_process_image_returns_faces(
        self,
        processor: FaceProcessor,
        tmp_path: Path,
    ) -> None:
        """Should detect faces and return encodings."""
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake_image_data")

        results = processor.process_image(img_path)

        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert isinstance(r, FaceResult)
            assert r.encoding.shape == (128,)
            assert len(r.location) == 4
            assert all(isinstance(x, int) for x in r.location)

    def test_blur_rejection(
        self,
        processor: FaceProcessor,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should reject blurry images."""
        img_path = tmp_path / "blurry.jpg"
        img_path.write_bytes(b"blurry_image")

        monkeypatch.setattr(
            processor,
            "_passes_blur_check",
            lambda image: False,
        )

        with pytest.raises(BlurError):
            processor.process_image(img_path)

    def test_cnn_fallback_to_hog(
        self,
        processor: FaceProcessor,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should fall back to HOG when CNN finds 0 faces."""
        img_path = tmp_path / "noface.jpg"
        img_path.write_bytes(b"no_face_here")

        def mock_locations(
            img: np.ndarray,
            number_of_times_to_upsample: int = 1,
            model: str = "hog",
        ) -> list[tuple[int, int, int, int]]:
            return [] if model == "cnn" else [(10, 60, 60, 10)]

        monkeypatch.setattr(
            processor._fr,
            "face_locations",
            mock_locations,
        )

        results = processor.process_image(img_path)
        assert len(results) == 1

    def test_no_faces_returns_empty(
        self,
        processor: FaceProcessor,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Should return empty list when no faces detected."""
        img_path = tmp_path / "empty.jpg"
        img_path.write_bytes(b"no_faces")

        monkeypatch.setattr(
            processor._fr,
            "face_locations",
            lambda *a, **k: [],
        )

        results = processor.process_image(img_path)
        assert results == []

    def test_encoding_dimensions(
        self,
        processor: FaceProcessor,
        tmp_path: Path,
    ) -> None:
        """All encodings must be exactly 128 dimensions."""
        img_path = tmp_path / "face.jpg"
        img_path.write_bytes(b"one_face")

        results = processor.process_image(img_path)
        for r in results:
            assert r.encoding.shape == (128,)
            assert r.encoding.dtype == np.float32
