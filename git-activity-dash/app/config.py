"""Application configuration."""

import os
import yaml
from pathlib import Path


class Config:
    """Base configuration class."""

    BASE_DIR = Path(__file__).parent.parent

    # Load config.yaml
    config_path = BASE_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            YAML_CONFIG = yaml.safe_load(f)
    else:
        YAML_CONFIG = {}

    # App settings
    APP_CONFIG = YAML_CONFIG.get("app", {})
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = APP_CONFIG.get("debug", False)

    # Repository settings
    REPO_CONFIG = YAML_CONFIG.get("repositories", {})
    ALLOWED_PATHS = REPO_CONFIG.get("allowed_paths", ["/home/user/repos"])
    DEFAULT_PATH = REPO_CONFIG.get("default_path", "/home/user/repos")

    # Analysis settings
    ANALYSIS_CONFIG = YAML_CONFIG.get("analysis", {})
    DEFAULT_PAGE_SIZE = ANALYSIS_CONFIG.get("default_page_size", 50)
    MAX_PAGE_SIZE = ANALYSIS_CONFIG.get("max_page_size", 200)
    TIMEOUT_SECONDS = ANALYSIS_CONFIG.get("timeout_seconds", 30)

    # Cache settings
    CACHE_CONFIG = YAML_CONFIG.get("cache", {})
    CACHE_ENABLED = CACHE_CONFIG.get("enabled", True)
    CACHE_TTL_MINUTES = CACHE_CONFIG.get("ttl_minutes", 5)

    # Cache TTLs in seconds
    CACHE_TTL = {
        "repo_info": 300,
        "commits": 60,
        "contributors": 300,
        "activity": 300,
        "files": 300,
        "branches": 300,
        "messages": 300,
    }

    @classmethod
    def is_path_allowed(cls, path: str) -> bool:
        """Check if the given path is within allowed paths."""
        if not cls.ALLOWED_PATHS:
            return True

        abs_path = os.path.abspath(path)
        for allowed in cls.ALLOWED_PATHS:
            allowed_abs = os.path.abspath(allowed)
            if abs_path.startswith(allowed_abs):
                return True
        return False


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
