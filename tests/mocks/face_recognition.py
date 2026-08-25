"""Deterministic mock of face_recognition for CI and fast tests."""

import hashlib
from pathlib import Path
from typing import BinaryIO

import numpy as np


def _hash_to_bytes(data: bytes, length: int) -> bytes:
    """Expand SHA-256 hash to arbitrary length deterministically."""
    hash_obj = hashlib.sha256(data)
    digest = hash_obj.digest()
    repeated = digest * (length // len(digest) + 1)
    return repeated[:length]


def load_image_file(file: str | Path | BinaryIO) -> np.ndarray:
    """Return a deterministic RGB image array."""
    if isinstance(file, (str, Path)):
        with open(file, "rb") as f:
            data = f.read()
    else:
        data = file.read()

    seed = int(_hash_to_bytes(data, 4).hex(), 16)
    h = (seed % 200) + 100
    w = ((seed // 256) % 200) + 100

    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, :, 0] = np.arange(w, dtype=np.uint8) * 17
    arr[:, :, 1] = np.arange(h, dtype=np.uint8)[:, None] * 13
    arr[:, :, 2] = seed % 256
    return arr


def face_locations(
    img: np.ndarray,
    number_of_times_to_upsample: int = 1,
    model: str = "hog",
) -> list[tuple[int, int, int, int]]:
    """Return deterministic face locations based on image dimensions."""
    h, w = img.shape[:2]
    seed = h * 1000 + w
    count = seed % 5

    locations: list[tuple[int, int, int, int]] = []
    for i in range(count):
        top = (seed + i * 50) % max(1, h - 50)
        left = (seed + i * 70) % max(1, w - 50)
        right = min(left + 50 + (seed % 30), w)
        bottom = min(top + 50 + (seed % 20), h)
        locations.append((top, right, bottom, left))
    return locations


def face_encodings(
    face_image: np.ndarray,
    known_face_locations: list[tuple[int, int, int, int]] | None = None,
    num_jitters: int = 1,
    model: str = "small",
) -> list[np.ndarray]:
    """Return deterministic 128-dim encodings."""
    if known_face_locations is None:
        known_face_locations = face_locations(face_image)

    encodings: list[np.ndarray] = []
    for loc in known_face_locations:
        key = str(loc).encode()
        raw = _hash_to_bytes(key, 128 * 4)
        arr = np.frombuffer(raw, dtype=np.float32).copy()
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        encodings.append(arr)
    return encodings


def face_distance(
    face_encodings: list[np.ndarray],
    face_to_compare: np.ndarray,
) -> np.ndarray:
    """Compute Euclidean distances."""
    if len(face_encodings) == 0:
        return np.array([])
    encs = np.array(face_encodings)
    target = np.array(face_to_compare)
    return np.linalg.norm(encs - target, axis=1)
