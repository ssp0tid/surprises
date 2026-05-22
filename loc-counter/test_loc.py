import json
import tempfile
from pathlib import Path

from counter import count_file, summarize_by_language
from formatters import format_csv, format_json, format_table
from gitignore import is_ignored, parse_gitignore
from languages import LangDef, get_language


def test_get_language_by_extension():
    lang = get_language("main.py", ".py")
    assert lang is not None
    assert lang.name == "Python"

    lang = get_language("app.js", ".js")
    assert lang is not None
    assert lang.name == "JavaScript"

    assert get_language("data.xyz", ".xyz") is None


def test_get_language_by_filename():
    lang = get_language("Makefile", "")
    assert lang is not None
    assert lang.name == "Makefile"

    lang = get_language("Dockerfile", "")
    assert lang is not None
    assert lang.name == "Dockerfile"


def test_count_file_python():
    content = """# This is a comment
import os

def hello():
    pass
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    lang_def = get_language(filepath.name, filepath.suffix)
    stats = count_file(filepath, lang_def)

    assert stats.code == 3
    assert stats.comments == 1
    assert stats.blanks == 1
    assert stats.total == 5
    filepath.unlink()


def test_count_file_block_comments():
    content = """/* This is
a block comment */
int main() {
    return 0;
}
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    lang_def = get_language(filepath.name, filepath.suffix)
    stats = count_file(filepath, lang_def)

    assert stats.comments == 2
    assert stats.code == 3
    assert stats.blanks == 0
    filepath.unlink()


def test_count_file_single_line_block_comment():
    content = """/* single line block */
int x = 1;
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        f.write(content)
        f.flush()
        filepath = Path(f.name)

    lang_def = get_language(filepath.name, filepath.suffix)
    stats = count_file(filepath, lang_def)

    assert stats.comments == 1
    assert stats.code == 1
    filepath.unlink()


def test_summarize_by_language():
    from counter import FileStats

    file_stats = [
        FileStats("a.py", "Python", 10, 2, 3, 15),
        FileStats("b.py", "Python", 20, 5, 4, 29),
        FileStats("c.js", "JavaScript", 15, 3, 2, 20),
    ]
    summaries = summarize_by_language(file_stats)
    assert len(summaries) == 2

    py = next(s for s in summaries if s.language == "Python")
    assert py.files == 2
    assert py.code == 30
    assert py.comments == 7
    assert py.blanks == 7

    js = next(s for s in summaries if s.language == "JavaScript")
    assert js.files == 1
    assert js.code == 15


def test_format_json():
    from counter import LangSummary

    summaries = [LangSummary("Python", 2, 30, 7, 7, 44)]
    total = LangSummary("Total", 2, 30, 7, 7, 44)
    output = format_json(summaries, total)
    data = json.loads(output)

    assert len(data["languages"]) == 1
    assert data["languages"][0]["language"] == "Python"
    assert data["total"]["code"] == 30


def test_format_csv():
    from counter import LangSummary

    summaries = [LangSummary("Python", 2, 30, 7, 7, 44)]
    total = LangSummary("Total", 2, 30, 7, 7, 44)
    output = format_csv(summaries, total)
    lines = output.strip().splitlines()

    assert lines[0] == "Language,Files,Code,Comments,Blanks,Total"
    assert "Python" in lines[1]
    assert "Total" in lines[2]


def test_format_table():
    from counter import LangSummary

    summaries = [LangSummary("Python", 2, 30, 7, 7, 44)]
    total = LangSummary("Total", 2, 30, 7, 7, 44)
    output = format_table(summaries, total)

    assert "Python" in output
    assert "Total" in output
    assert "\u2500" in output


def test_gitignore_parse():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        gitignore = root / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n# comment\n\n*.log\n")

        patterns = parse_gitignore(root)
        assert "*.pyc" in patterns
        assert "__pycache__" in patterns
        assert "*.log" in patterns
        assert len(patterns) == 3


def test_is_ignored():
    root = Path("/project")
    patterns = ["*.pyc", "dist"]

    assert is_ignored(Path("/project/foo.pyc"), root, patterns) is True
    assert is_ignored(Path("/project/foo.py"), root, patterns) is False
    assert is_ignored(Path("/project/dist/bundle.js"), root, patterns) is True


if __name__ == "__main__":
    test_get_language_by_extension()
    test_get_language_by_filename()
    test_count_file_python()
    test_count_file_block_comments()
    test_count_file_single_line_block_comment()
    test_summarize_by_language()
    test_format_json()
    test_format_csv()
    test_format_table()
    test_gitignore_parse()
    test_is_ignored()
    print("All tests passed!")
