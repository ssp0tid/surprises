"""Script to generate test repositories."""

import subprocess
from pathlib import Path
import tempfile


def create_simple_repo(path: Path) -> None:
    """Create a simple git repository."""
    path.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    (path / "README.md").write_text("# Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def create_branched_repo(path: Path) -> None:
    """Create a repository with branches."""
    create_simple_repo(path)

    (path / "feature.txt").write_text("Feature file\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add feature file"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "checkout", "-b", "feature/login"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    (path / "login.py").write_text("# Login module\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add login module"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "checkout", "main"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def main():
    """Generate all test repositories."""
    script_dir = Path(__file__).parent
    fixtures_dir = script_dir.parent / "tests" / "fixtures"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        simple_path = tmpdir / "simple_repo"
        create_simple_repo(simple_path)
        dest_simple = fixtures_dir / "simple_repo"
        if dest_simple.exists():
            import shutil

            shutil.rmtree(dest_simple)
        shutil.copytree(simple_path, dest_simple)

        branched_path = tmpdir / "branched_repo"
        create_branched_repo(branched_path)
        dest_branched = fixtures_dir / "branched_repo"
        if dest_branched.exists():
            shutil.rmtree(dest_branched)
        shutil.copytree(branched_path, dest_branched)

    print("Test repositories created successfully!")


if __name__ == "__main__":
    main()
