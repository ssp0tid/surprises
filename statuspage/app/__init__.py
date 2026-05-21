import logging
import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    from app.config import config

    app.config.from_object(config.get(config_name, config["default"]))

    ensure_directories(app)
    setup_logging(app)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    register_blueprints(app)
    register_filters(app)

    with app.app_context():
        if app.config.get("START_SCHEDULER", True):
            from app.services.scheduler import start_scheduler

            start_scheduler(app)
        db.create_all()
        init_first_run(app)

    return app


def ensure_directories(app):
    instance_dir = Path(app.instance_path)
    instance_dir.mkdir(parents=True, exist_ok=True)

    (instance_dir / "uploads").mkdir(exist_ok=True)
    (instance_dir.parent / "logs").mkdir(exist_ok=True)


def setup_logging(app):
    log_file = app.config.get("LOG_FILE")
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=app.config.get("LOG_LEVEL", "INFO"),
            format="%(asctime)s %(levelname)s: %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )


def register_blueprints(app):
    from app.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.status import status_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(status_bp, url_prefix="/status")
    app.register_blueprint(api_bp, url_prefix="/api")


def register_filters(app):
    from app.utils.helpers import format_datetime, format_relative_time, status_badge

    app.jinja_env.filters["datetime"] = format_datetime
    app.jinja_env.filters["relative_time"] = format_relative_time
    app.jinja_env.filters["status_badge"] = status_badge


def init_first_run(app):
    import json
    from app.models import Organization, User

    if Organization.query.count() == 0:
        org = Organization(
            name="My Organization",
            slug="my-org",
            custom_branding=json.dumps(
                {
                    "primary_color": "#2563eb",
                    "logo": None,
                    "custom_css": "",
                }
            ),
        )
        db.session.add(org)
        db.session.commit()

        app.logger.info(f"Created default organization: {org.slug}")
