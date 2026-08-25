"""Wedding Face Finder — AI Face Recognition for Event Photography.

A production-grade Flask application for scanning event photos and matching
guests via face recognition. Built with security, privacy, and scalability
in mind.
"""

__version__ = "0.1.0"

from wedding_face_finder.app import create_app

__all__ = ["create_app", "__version__"]
