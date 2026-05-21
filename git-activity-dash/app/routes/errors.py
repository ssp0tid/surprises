"""Error handlers."""

from flask import Flask, jsonify

from app.utils.validators import ValidationError


class APIError(Exception):
    """Base API error."""

    def __init__(self, message: str, code: str, status_code: int, details: str = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class RepositoryNotFoundError(APIError):
    """Raised when repository is not found."""

    def __init__(self, path: str):
        super().__init__("Repository path does not exist", "REPO_NOT_FOUND", 404, path)


class NotGitRepositoryError(APIError):
    """Raised when path is not a git repository."""

    def __init__(self, path: str):
        super().__init__("Not a valid git repository", "NOT_GIT_REPO", 422, path)


class InvalidPathError(APIError):
    """Raised when path is invalid."""

    def __init__(self, message: str = "Invalid path"):
        super().__init__(message, "INVALID_PATH", 400)


def register_error_handlers(app: Flask):
    """Register error handlers on Flask app."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify(
            {
                "error": {
                    "code": e.code,
                    "message": str(e),
                    "details": e.args[2] if len(e.args) > 2 else None,
                }
            }
        ), e.status_code if len(e.args) > 1 else 400

    @app.errorhandler(APIError)
    def handle_api_error(e):
        return jsonify(
            {"error": {"code": e.code, "message": e.message, "details": e.details}}
        ), e.status_code

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(
            {
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "Bad request",
                    "details": str(e),
                }
            }
        ), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": str(e),
                }
            }
        ), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify(
            {
                "error": {
                    "code": "UNPROCESSABLE",
                    "message": "Unprocessable entity",
                    "details": str(e),
                }
            }
        ), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": str(e),
                }
            }
        ), 500
