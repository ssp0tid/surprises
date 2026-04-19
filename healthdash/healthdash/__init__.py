from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError

from .config import config
from .models import db


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    csrf = CSRFProtect(app)

    from .api.routes import api_bp
    from .web.routes import web_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return jsonify({"error": "CSRF token expired or invalid"}), 400

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    with app.app_context():
        db.create_all()

    from .services.scheduler import schedule_service_checks

    schedule_service_checks(app)

    return app


def create_db():
    from flask import current_app

    with current_app.app_context():
        db.create_all()
