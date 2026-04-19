import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///healthdash.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Scheduler
    SCHEDULER_API_ENABLED = False

    # Health check defaults
    DEFAULT_TIMEOUT = 10
    DEFAULT_INTERVAL = 60
    MAX_HISTORY_PER_SERVICE = 1000


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
