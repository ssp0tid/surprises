import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32).hex())

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR}/statuspage.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days

    # Upload
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    UPLOAD_FOLDER = INSTANCE_DIR / "uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg"}

    # Defaults
    DEFAULT_CHECK_INTERVAL = 60  # seconds
    DEFAULT_CHECK_TIMEOUT = 30  # seconds
    DEFAULT_EXPECTED_STATUS = 200

    # Logging
    LOG_FILE = BASE_DIR / "logs" / "app.log"
    LOG_LEVEL = "INFO"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
