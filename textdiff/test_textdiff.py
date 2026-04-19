#!/usr/bin/env python3
"""Test suite for textdiff.py"""

import subprocess
import tempfile
import os
import sys


def run_textdiff(*args):
    result = subprocess.run(
        [sys.executable, "textdiff.py"] + list(args),
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
    )
    return result


def test_identical_files():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nline 2\nline 3\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nline 2\nline 3\n")
        f2 = f.name

    result = run_textdiff(f1, f2)
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0
    assert result.stdout.strip() != ""


def test_simple_diff():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nline 2\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nline 2\nline 3\n")
        f2 = f.name

    result = run_textdiff(f1, f2)
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0
    assert "line 3" in result.stdout


def test_deletion():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nline 2\nline 3\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nline 2\n")
        f2 = f.name

    result = run_textdiff(f1, f2)
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0


def test_modification():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nold line\nline 3\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nnew line\nline 3\n")
        f2 = f.name

    result = run_textdiff(f1, f2)
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0
    assert "old line" in result.stdout or "new line" in result.stdout


def test_missing_file():
    result = run_textdiff("/nonexistent/file.txt", "/another/missing.txt")
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()


def test_binary_file():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        f.write(b"line 1\n\x00binary content\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\ntext content\n")
        f2 = f.name

    result = run_textdiff(f1, f2)
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode != 0
    assert "binary" in result.stderr.lower()


def test_empty_files():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("")
        f2 = f.name

    result = run_textdiff(f1, f2)
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0


def test_inline_mode():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nb\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nc\n")
        f2 = f.name

    result = run_textdiff(f1, f2, "--inline")
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0
    assert "Inline" in result.stdout


def test_unified_mode():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nb\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nc\n")
        f2 = f.name

    result = run_textdiff(f1, f2, "-u")
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0
    assert "Unified" in result.stdout


def test_ignore_whitespace():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\n  spaces  \nline 3\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line 1\nspaces\nline 3\n")
        f2 = f.name

    result = run_textdiff(f1, f2, "-w")
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0


def test_no_color():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nb\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nc\n")
        f2 = f.name

    result = run_textdiff(f1, f2, "--no-color")
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0
    assert "\033[" not in result.stdout


def test_context_lines():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nb\nc\nd\ne\n")
        f1 = f.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a\nb\nc\nd\nx\n")
        f2 = f.name

    result = run_textdiff(f1, f2, "-u", "-c", "5")
    os.unlink(f1)
    os.unlink(f2)

    assert result.returncode == 0


if __name__ == "__main__":
    tests = [
        test_identical_files,
        test_simple_diff,
        test_deletion,
        test_modification,
        test_missing_file,
        test_binary_file,
        test_empty_files,
        test_inline_mode,
        test_unified_mode,
        test_ignore_whitespace,
        test_no_color,
        test_context_lines,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__} - {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    sys.exit(0 if failed == 0 else 1)
