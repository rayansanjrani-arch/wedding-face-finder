import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "ADMIN_PASSWORD_HASH",
    "$2b$04$3EKbDPV3JDkQT2WSb6Rm4ejxR3mYu9YOJiX/AY2QlQXNgS6QY5uOO"
)