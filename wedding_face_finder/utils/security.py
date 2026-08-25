"""Password hashing and token utilities."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash password with bcrypt (work factor 12)."""
    pw_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    pw_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hash_bytes)
