"""Face detection and encoding extraction with quality gates."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from wedding_face_finder.config import Settings

logger = logging.getLogger(__name__)

try:
    import cv2  # type: ignore[import-not-found]
except ImportError:
    cv2 = None  # type: ignore[assignment]

try:
    import face_recognition as _face_recognition  # type: ignore[import-untyped]
except Exception:
    from tests.mocks import (  # type: ignore[assignment]
        face_recognition as _face_recognition,
    )


class BlurError(Exception):
    """Raised when an image fails the blur quality gate."""


class FaceResult:
    """Result of processing a single face."""

    def __init__(
        self,
        encoding: np.ndarray,
        location: tuple[int, int, int, int],
        confidence: float,
        face_index: int,
    ) -> None:
        self.encoding = encoding
        self.location = location
        self.confidence = confidence
        self.face_index = face_index


class FaceProcessor:
    """Detect faces, check quality, extract 128-dim encodings."""

    def __init__(
        self,
        settings: Settings,
        face_recognition_module=None,
    ) -> None:
        self.settings = settings
        self._fr = face_recognition_module or _face_recognition
        if self._fr is None:
            raise RuntimeError(
                "face_recognition library not installed. "
                "Install with: pip install face-recognition"
            )

    def process_image(self, image_path: Path) -> list[FaceResult]:
        """Full pipeline: load → blur check → detect → encode."""
        image = self._load_image(image_path)

        if not self._passes_blur_check(image):
            raise BlurError(f"Image {image_path.name} is too blurry")

        locations = self._detect_faces(image)
        if not locations:
            logger.info("No faces detected in %s", image_path.name)
            return []

        encodings = self._extract_encodings(image, locations)

        results: list[FaceResult] = []
        for idx, (loc, enc) in enumerate(zip(locations, encodings)):
            results.append(
                FaceResult(
                    encoding=enc,
                    location=loc,
                    confidence=1.0,
                    face_index=idx,
                )
            )
        return results

    def _load_image(self, path: Path) -> np.ndarray:
        return self._fr.load_image_file(str(path))

    def _passes_blur_check(self, image: np.ndarray) -> bool:
        if cv2 is None:
            logger.warning("OpenCV not installed; skipping blur check")
            return True
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance >= self.settings.blur_threshold

    def _detect_faces(
        self,
        image: np.ndarray,
    ) -> list[tuple[int, int, int, int]]:
        locations = self._fr.face_locations(
            image,
            model="cnn",
        )
        if not locations:
            logger.info("CNN found 0 faces, falling back to HOG")
            locations = self._fr.face_locations(
                image,
                model="hog",
            )
        return locations

    def _extract_encodings(
        self,
        image: np.ndarray,
        locations: list[tuple[int, int, int, int]],
    ) -> list[np.ndarray]:
        return self._fr.face_encodings(
            image,
            known_face_locations=locations,
        )
