import re
import shutil

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax


class Renderer:
    def __init__(self) -> None:
        self.console = Console()
        self._language_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "sh": "bash",
            "yml": "yaml",
            "md": "markdown",
            "rs": "rust",
            "go": "go",
            "json": "json",
        }

    def render(self, markdown_text: str) -> None:
        if not markdown_text:
            return

        try:
            markdown_text = self._preprocess(markdown_text)
            md = Markdown(markdown_text)
            self.console.print(md)
        except Exception:
            self.console.print(markdown_text)

    def _preprocess(self, text: str) -> str:
        code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

        def replace_code_block(match: re.Match) -> str:
            lang = match.group(1) or "text"
            code = match.group(2)
            lang = self._language_map.get(lang, lang)
            width = shutil.get_terminal_size().columns or 80
            syntax = Syntax(code, lang, theme="monokai", line_numbers=True, width=width)
            return f"```\n{syntax}```"

        return code_block_pattern.sub(replace_code_block, text)
