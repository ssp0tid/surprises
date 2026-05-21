"""API endpoints."""

import os
from flask import Blueprint, jsonify, request

from app.services import GitAnalyzer, CommitAnalyzer, ContribAnalyzer, FileAnalyzer
from app.utils.validators import (
    ValidationError,
    validate_repo_path,
    validate_git_repository,
    validate_pagination,
    validate_date_range,
)
from app.config import Config
from app.routes.errors import RepositoryNotFoundError, NotGitRepositoryError

api_bp = Blueprint("api", __name__)


def _serialize_datetime(dt):
    """Serialize datetime to ISO format."""
    if dt is None:
        return None
    return dt.isoformat()


def _serialize_repo(repo):
    """Serialize repository info."""
    return {
        "path": repo.path,
        "name": repo.name,
        "is_valid": repo.is_valid,
        "branch_count": repo.branch_count,
        "total_commits": repo.total_commits,
        "contributors": [
            {
                "name": c.name,
                "email": c.email,
                "commit_count": c.commit_count,
                "first_commit": _serialize_datetime(c.first_commit),
                "last_commit": _serialize_datetime(c.last_commit),
                "insertions": c.insertions,
                "deletions": c.deletions,
            }
            for c in repo.contributors
        ],
        "first_commit_date": _serialize_datetime(repo.first_commit_date),
        "last_commit_date": _serialize_datetime(repo.last_commit_date),
    }


def _serialize_commit(commit):
    """Serialize commit info."""
    return {
        "sha": commit.sha,
        "short_sha": commit.short_sha,
        "author": {"name": commit.author.name, "email": commit.author.email},
        "committer": {"name": commit.committer.name, "email": commit.committer.email},
        "message": commit.message,
        "message_first_line": commit.message_first_line,
        "date": _serialize_datetime(commit.date),
        "changed_files": commit.changed_files,
        "insertions": commit.insertions,
        "deletions": commit.deletions,
    }


def _serialize_contributor(contributor):
    """Serialize contributor info."""
    return {
        "name": contributor.name,
        "email": contributor.email,
        "commit_count": contributor.commit_count,
        "first_commit": _serialize_datetime(contributor.first_commit),
        "last_commit": _serialize_datetime(contributor.last_commit),
        "insertions": contributor.insertions,
        "deletions": contributor.deletions,
    }


def _serialize_activity_hour(activity):
    """Serialize activity hour."""
    return {
        "hour": activity.hour,
        "day": activity.day,
        "commit_count": activity.commit_count,
    }


def _serialize_file_change(file_change):
    """Serialize file change."""
    return {
        "path": file_change.path,
        "change_count": file_change.change_count,
        "insertions": file_change.insertions,
        "deletions": file_change.deletions,
        "last_changed": _serialize_datetime(file_change.last_changed),
    }


def _serialize_branch(branch):
    """Serialize branch info."""
    return {
        "name": branch.name,
        "is_remote": branch.is_remote,
        "is_current": branch.is_current,
        "last_commit_sha": branch.last_commit_sha,
        "last_commit_date": _serialize_datetime(branch.last_commit_date),
        "commit_count": branch.commit_count,
    }


def _serialize_message_analysis(msg):
    """Serialize message analysis."""
    return {
        "category": msg.category,
        "count": msg.count,
        "percentage": msg.percentage,
        "examples": msg.examples,
    }


@api_bp.route("/repos")
def list_repos():
    """List available local repositories."""
    default_path = request.args.get("path", Config.DEFAULT_PATH)

    if not os.path.exists(default_path):
        return jsonify({"repos": []})

    repos = []
    try:
        for entry in os.listdir(default_path):
            entry_path = os.path.join(default_path, entry)
            if os.path.isdir(entry_path):
                git_dir = os.path.join(entry_path, ".git")
                is_valid = os.path.isdir(git_dir)
                error = None if is_valid else "Not a git repository"

                repos.append(
                    {
                        "path": entry_path,
                        "name": entry,
                        "valid": is_valid,
                        "error": error,
                    }
                )
    except PermissionError:
        return jsonify({"repos": []})

    return jsonify({"repos": repos})


@api_bp.route("/repo/<path:repo_path>/info")
def repo_info(repo_path: str):
    """Get repository overview stats."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        analyzer = GitAnalyzer(validated_path)
        try:
            repo_info_data = analyzer.get_repository_info()
        finally:
            analyzer.close()

        return jsonify(_serialize_repo(repo_info_data))

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code


@api_bp.route("/repo/<path:repo_path>/commits")
def repo_commits(repo_path: str):
    """Get paginated commit history."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", Config.DEFAULT_PAGE_SIZE, type=int)
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        page, per_page = validate_pagination(page, per_page, Config.MAX_PAGE_SIZE)
        start_dt, end_dt = validate_date_range(start_date, end_date)

        analyzer = GitAnalyzer(validated_path)
        try:
            commit_analyzer = CommitAnalyzer(analyzer.repo)
            commits, total = commit_analyzer.get_commits(
                page, per_page, start_dt, end_dt
            )
        finally:
            analyzer.close()

        return jsonify(
            {
                "commits": [_serialize_commit(c) for c in commits],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page,
                },
            }
        )

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code


@api_bp.route("/repo/<path:repo_path>/contributors")
def repo_contributors(repo_path: str):
    """Get contributor statistics."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        analyzer = GitAnalyzer(validated_path)
        try:
            contrib_analyzer = ContribAnalyzer(analyzer.repo)
            contributors = contrib_analyzer.get_contributors()
        finally:
            analyzer.close()

        return jsonify(
            {"contributors": [_serialize_contributor(c) for c in contributors]}
        )

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code


@api_bp.route("/repo/<path:repo_path>/activity")
def repo_activity(repo_path: str):
    """Get hourly/daily activity data."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        analyzer = GitAnalyzer(validated_path)
        try:
            contrib_analyzer = ContribAnalyzer(analyzer.repo)
            activity = contrib_analyzer.get_activity_heatmap()
        finally:
            analyzer.close()

        return jsonify({"activity": [_serialize_activity_hour(a) for a in activity]})

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code


@api_bp.route("/repo/<path:repo_path>/files")
def repo_files(repo_path: str):
    """Get file change statistics."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        limit = request.args.get("limit", 50, type=int)

        analyzer = GitAnalyzer(validated_path)
        try:
            file_analyzer = FileAnalyzer(analyzer.repo)
            files = file_analyzer.get_file_changes(limit)
        finally:
            analyzer.close()

        return jsonify({"files": [_serialize_file_change(f) for f in files]})

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code


@api_bp.route("/repo/<path:repo_path>/branches")
def repo_branches(repo_path: str):
    """Get branch information."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        analyzer = GitAnalyzer(validated_path)
        try:
            file_analyzer = FileAnalyzer(analyzer.repo)
            branches = file_analyzer.get_branches()
        finally:
            analyzer.close()

        return jsonify({"branches": [_serialize_branch(b) for b in branches]})

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code


@api_bp.route("/repo/<path:repo_path>/messages")
def repo_messages(repo_path: str):
    """Get commit message analysis."""
    try:
        validated_path = validate_repo_path(repo_path)
        validate_git_repository(validated_path)

        analyzer = GitAnalyzer(validated_path)
        try:
            file_analyzer = FileAnalyzer(analyzer.repo)
            messages = file_analyzer.analyze_messages()
        finally:
            analyzer.close()

        return jsonify({"messages": [_serialize_message_analysis(m) for m in messages]})

    except ValidationError as e:
        if e.code == "REPO_NOT_FOUND":
            raise RepositoryNotFoundError(repo_path)
        elif e.code == "NOT_GIT_REPO":
            raise NotGitRepositoryError(repo_path)
        return jsonify({"error": {"code": e.code, "message": str(e)}}), e.status_code
