"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_repo(temp_dir):
    """Create a simple git repository for testing."""
    repo_path = temp_dir / "simple_repo"
    repo_path.mkdir()

    git_dir = repo_path / ".git"
    git_dir.mkdir()

    (git_dir / "objects").mkdir()
    (git_dir / "refs" / "heads").mkdir(parents=True)

    head_content = "ref: refs/heads/main\n"
    (git_dir / "HEAD").write_text(head_content)

    (git_dir / "refs" / "heads" / "main").write_text("a" * 40 + "\n")

    return repo_path


@pytest.fixture
def branched_repo(temp_dir):
    """Create a repository with branches for testing."""
    repo_path = temp_dir / "branched_repo"
    repo_path.mkdir()

    git_dir = repo_path / ".git"
    git_dir.mkdir()

    (git_dir / "objects").mkdir()
    (git_dir / "refs" / "heads").mkdir(parents=True)

    return repo_path
