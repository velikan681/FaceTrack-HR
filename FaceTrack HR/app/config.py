import os
from datetime import timedelta


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(PROJECT_ROOT, "instance")
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "app", "static", "uploads")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'app.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    UPLOAD_FOLDER = UPLOAD_DIR
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}

    # Face recognition parameters.
    RECOGNITION_TOLERANCE = float(os.environ.get("RECOGNITION_TOLERANCE", "0.45"))

    # Attendance logic parameters.
    DUPLICATE_INTERVAL_MINUTES = int(os.environ.get("DUPLICATE_INTERVAL_MINUTES", "2"))
    MIN_CHECKOUT_MINUTES = int(os.environ.get("MIN_CHECKOUT_MINUTES", "30"))
    LATE_AFTER = os.environ.get("LATE_AFTER", "09:15")
