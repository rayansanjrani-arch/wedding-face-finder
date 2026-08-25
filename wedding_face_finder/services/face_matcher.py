"""Face matching engine with linear scan and tolerance filtering."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from wedding_face_finder.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class Match:
    """A single face match result."""

    photo_id: int
    face_index: int
    distance: float
    confidence: float


class FaceMatcher:
    """Compare face encodings against candidates."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def find_matches(
        self,
        query_encoding: np.ndarray,
        candidates: list[tuple[int, int, np.ndarray]],
    ) -> list[Match]:
        """Find candidates within tolerance, sorted by distance."""
        if len(query_encoding) != 128:
            raise ValueError("Query encoding must be 128-dimensional")

        matches: list[Match] = []
        tolerance = self.settings.tolerance

        for photo_id, face_index, encoding in candidates:
            if len(encoding) != 128:
                logger.warning(
                    "Skipping malformed encoding for photo_id=%s",
                    photo_id,
                )
                continue

            distance = float(np.linalg.norm(query_encoding - encoding))

            if distance <= tolerance:
                confidence = max(0.0, 1.0 - (distance / tolerance))
                matches.append(
                    Match(
                        photo_id=photo_id,
                        face_index=face_index,
                        distance=distance,
                        confidence=confidence,
                    )
                )

        matches.sort(key=lambda m: m.distance)
        return matches
