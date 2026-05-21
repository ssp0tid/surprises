"""Main routes for the application."""

import os
from flask import Blueprint, render_template, request, redirect, url_for

from app.services import GitAnalyzer
from app.utils.validators import (
    ValidationError,
    validate_repo_path,
    validate_git_repository,
)
from app.routes.errors import (
    RepositoryNotFoundError,
    NotGitRepositoryError,
    InvalidPathError,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page with repository selection."""
    default_path = os.environ.get("HOME", os.getcwd())
    return render_template("index.html", default_path=default_path)


@main_bp.route("/dashboard/<path:repo_path>")
def dashboard(repo_path: str):
    """Dashboard page for repository analysis."""
    try:
        validated_path = validate_repo_path(repo_path)

        if not os.path.isdir(validated_path):
            raise RepositoryNotFoundError(validated_path)

        try:
            validate_git_repository(validated_path)
        except ValidationError as e:
            if e.code == "REPO_NOT_FOUND":
                raise RepositoryNotFoundError(validated_path)
            raise NotGitRepositoryError(validated_path)

        analyzer = GitAnalyzer(validated_path)
        try:
            repo_info = analyzer.get_repository_info()
        finally:
            analyzer.close()

        return render_template(
            "dashboard.html",
            repo=repo_info,
            repo_path=repo_path,
            repo_path_js=repo_path,
        )

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(
                validated_path if "validated_path" in locals() else repo_path
            )
        raise
