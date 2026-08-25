"""Database utilities for Alembic and raw SQLAlchemy operations.

Flask-SQLAlchemy handles ORM and sessions via the 'db' extension.
This module provides Alembic-compatible metadata and engine access.
"""

from wedding_face_finder.extensions import db

# Alembic target metadata — points to Flask-SQLAlchemy's model registry
target_metadata = db.Model.metadata
