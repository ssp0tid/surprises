"""Language definitions for loc-counter."""

from dataclasses import dataclass


@dataclass
class LangDef:
    name: str
    extensions: list[str]
    line_comment: str | None
    block_comment_start: str | None
    block_comment_end: str | None


LANGUAGES: list[LangDef] = [
    LangDef("Python", [".py"], "#", None, None),
    LangDef("JavaScript", [".js", ".mjs"], "//", "/*", "*/"),
    LangDef("TypeScript", [".ts", ".tsx"], "//", "/*", "*/"),
    LangDef("Go", [".go"], "//", "/*", "*/"),
    LangDef("Rust", [".rs"], "//", "/*", "*/"),
    LangDef("C", [".c", ".h"], "//", "/*", "*/"),
    LangDef("C++", [".cpp", ".hpp", ".cc"], "//", "/*", "*/"),
    LangDef("Java", [".java"], "//", "/*", "*/"),
    LangDef("Ruby", [".rb"], "#", "=begin", "=end"),
    LangDef("Shell", [".sh", ".bash", ".zsh"], "#", None, None),
    LangDef("HTML", [".html", ".htm"], None, "<!--", "-->"),
    LangDef("CSS", [".css"], None, "/*", "*/"),
    LangDef("SCSS", [".scss"], "//", "/*", "*/"),
    LangDef("SQL", [".sql"], "--", "/*", "*/"),
    LangDef("Lua", [".lua"], "--", "--[[", "]]"),
    LangDef("Haskell", [".hs"], "--", "{-", "-}"),
    LangDef("YAML", [".yml", ".yaml"], "#", None, None),
    LangDef("TOML", [".toml"], "#", None, None),
    LangDef("Markdown", [".md"], None, None, None),
    LangDef("JSON", [".json"], None, None, None),
    LangDef("Kotlin", [".kt"], "//", "/*", "*/"),
    LangDef("Swift", [".swift"], "//", "/*", "*/"),
    LangDef("PHP", [".php"], "//", "/*", "*/"),
]

FILENAME_LANGUAGES: dict[str, LangDef] = {
    "Makefile": LangDef("Makefile", [], "#", None, None),
    "Dockerfile": LangDef("Dockerfile", [], "#", None, None),
}

EXT_TO_LANG: dict[str, LangDef] = {}
for lang in LANGUAGES:
    for ext in lang.extensions:
        EXT_TO_LANG[ext] = lang


def get_language(filepath_name: str, filepath_suffix: str) -> LangDef | None:
    """Get language definition for a file by name or extension."""
    if filepath_name in FILENAME_LANGUAGES:
        return FILENAME_LANGUAGES[filepath_name]
    return EXT_TO_LANG.get(filepath_suffix)
