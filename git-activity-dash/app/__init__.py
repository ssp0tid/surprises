"""Flask application factory."""

import logging
import os
from flask import Flask

from .config import config

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name (development, production)

    Returns:
        Configured Flask application
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, template_folder="templates", static_folder="../static")

    # Load configuration
    app.config.from_object(config.get(config_name, config["default"]))

    # Register blueprints
    from .routes import main_bp, api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Register error handlers
    from .routes.errors import register_error_handlers

    register_error_handlers(app)

    return app
