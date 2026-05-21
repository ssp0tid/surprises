"""Flask application factory."""

import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import get_config
from app.utils.errors import (
    HabitbeatError,
)

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    register_error_handlers(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app


def register_error_handlers(app):

    @app.errorhandler(HabitbeatError)
    def handle_habitbeat_error(error):
        return jsonify(
            {
                "error": {
                    "code": error.error_code,
                    "message": error.message,
                    "details": error.details,
                }
            }
        ), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify(
            {
                "error": {
                    "code": "BAD_REQUEST",
                    "message": str(error),
                    "details": [],
                }
            }
        ), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": [],
                }
            }
        ), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": [],
                }
            }
        ), 500


def register_blueprints(app):
    from app.api.habits import habits_bp
    from app.api.checkins import checkins_bp
    from app.api.categories import categories_bp
    from app.api.analytics import analytics_bp
    from app.api.reminders import reminders_bp
    from app.api.auth import auth_bp
    from app.routes.web import web_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(habits_bp, url_prefix="/api/habits")
    app.register_blueprint(checkins_bp, url_prefix="/api")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(reminders_bp, url_prefix="/api/reminders")
    app.register_blueprint(web_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})
