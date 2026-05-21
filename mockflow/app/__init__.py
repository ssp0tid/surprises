"""Flask application factory for MockFlow."""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from .config import get_config
from .models import db


def create_app(config_name=None):
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder="../static", template_folder="../templates")

    if config_name:
        app.config.from_object(config_name)
    else:
        app.config.from_object(get_config())

    db.init_app(app)
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    register_blueprints(app)
    register_error_handlers(app)
    register_routes(app)

    init_database(app)

    return app


def register_blueprints(app):
    """Register route blueprints."""
    from .routes import projects_bp, endpoints_bp, responses_bp, logs_bp, server_bp

    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(endpoints_bp, url_prefix="/api")
    app.register_blueprint(responses_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(server_bp, url_prefix="/api")


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(e):
        return {"error": "Bad request", "message": str(e)}, 400

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return {"error": "Internal server error"}, 500


def register_routes(app):
    """Register static and index routes."""

    @app.route("/")
    def index():
        return send_from_directory(app.template_folder, "index.html")

    @app.route("/<path:path>")
    def static_files(path):
        if path.startswith("api/"):
            return {"error": "Not found"}, 404
        return send_from_directory(app.static_folder, path)


def init_database(app):
    """Initialize database tables."""
    with app.app_context():
        db.create_all()


def register_matcher(app):
    """Register request matcher service."""
    from .services.matcher import RequestMatcher

    app.request_matcher = RequestMatcher(app)


def register_mock_server(app):
    """Register mock HTTP server service."""
    from .services.mock_server import MockServer

    app.mock_server = MockServer(app)
