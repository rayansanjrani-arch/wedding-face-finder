"""Unit tests for face matching engine."""

import numpy as np
import pytest

from wedding_face_finder.config import Settings
from wedding_face_finder.services.face_matcher import FaceMatcher


@pytest.fixture
def matcher(test_settings: Settings) -> FaceMatcher:
    """Return a FaceMatcher with test tolerance."""
    return FaceMatcher(settings=test_settings)


class TestFaceMatcher:
    """Test suite for face matching logic."""

    def test_find_matches_within_tolerance(
        self,
        matcher: FaceMatcher,
    ) -> None:
        """Should return candidates within tolerance, sorted."""
        query = np.zeros(128, dtype=np.float32)
        query[0] = 1.0

        candidates = [
            (1, 0, query.copy()),
            (2, 0, query * 0.9),
            (3, 0, np.ones(128) * 10),
        ]

        matches = matcher.find_matches(query, candidates)

        assert len(matches) == 2
        assert matches[0].photo_id == 1
        assert matches[1].photo_id == 2
        assert matches[0].distance <= matches[1].distance

    def test_empty_candidates(
        self,
        matcher: FaceMatcher,
    ) -> None:
        """Should return empty list when no candidates."""
        query = np.zeros(128, dtype=np.float32)
        matches = matcher.find_matches(query, [])
        assert matches == []

    def test_wrong_encoding_dimension(
        self,
        matcher: FaceMatcher,
    ) -> None:
        """Should raise ValueError for non-128-dim query."""
        query = np.zeros(64, dtype=np.float32)
        with pytest.raises(ValueError, match="128-dimensional"):
            matcher.find_matches(query, [])

    def test_malformed_candidate_skipped(
        self,
        matcher: FaceMatcher,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Should skip candidates with wrong encoding size."""
        query = np.zeros(128, dtype=np.float32)
        candidates = [
            (1, 0, query.copy()),
            (2, 0, np.zeros(64, dtype=np.float32)),
        ]

        matches = matcher.find_matches(query, candidates)
        assert len(matches) == 1
        assert matches[0].photo_id == 1
        assert "malformed encoding" in caplog.text

    def test_confidence_exact_match(
        self,
        matcher: FaceMatcher,
    ) -> None:
        """Exact match should have confidence 1.0."""
        query = np.zeros(128, dtype=np.float32)
        query[0] = 1.0

        matches = matcher.find_matches(query, [(1, 0, query.copy())])
        assert len(matches) == 1
        assert matches[0].confidence == 1.0

    def test_confidence_half_tolerance(
        self,
        matcher: FaceMatcher,
    ) -> None:
        """Half-tolerance distance should yield ~0.5 confidence."""
        query = np.zeros(128, dtype=np.float32)
        query[0] = 1.0

        offset = np.zeros(128, dtype=np.float32)
        offset[0] = matcher.settings.tolerance * 0.5

        matches = matcher.find_matches(
            query,
            [(2, 0, query + offset)],
        )
        assert len(matches) == 1
        assert 0.45 < matches[0].confidence < 0.55
