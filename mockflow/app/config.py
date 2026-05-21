"""Configuration settings for MockFlow Flask application."""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///mockflow.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Server settings
    DEFAULT_MOCK_SERVER_HOST = "0.0.0.0"
    DEFAULT_MOCK_SERVER_PORT = 8080
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Logging
    LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "7"))

    # Request limits
    MAX_ENDPOINTS_PER_PROJECT = int(os.environ.get("MAX_ENDPOINTS_PER_PROJECT", "100"))
    MAX_RESPONSES_PER_ENDPOINT = int(os.environ.get("MAX_RESPONSES_PER_ENDPOINT", "10"))

    # Response settings
    DEFAULT_RESPONSE_DELAY_MS = int(os.environ.get("DEFAULT_RESPONSE_DELAY_MS", "0"))
    MAX_RESPONSE_DELAY_MS = int(os.environ.get("MAX_RESPONSE_DELAY_MS", "30000"))


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False


# Configuration mapping
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Get configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
