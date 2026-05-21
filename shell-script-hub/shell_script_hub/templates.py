"""Template variable substitution system for shell-script-hub."""

import re
from typing import Any


class TemplateEngine:
    """Handles template variable substitution with {{variable}} syntax."""

    VAR_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

    def __init__(self, variables: dict[str, Any] | None = None):
        """Initialize with optional default variables."""
        self.variables = variables or {}

    def extract_variables(self, content: str) -> list[str]:
        """Extract all variable names from template content."""
        matches = self.VAR_PATTERN.findall(content)
        return list(dict.fromkeys(matches))

    def render(self, content: str, variables: dict[str, Any] | None = None) -> str:
        """Render template with provided variables."""
        vars_to_use = {**self.variables, **(variables or {})}

        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name in vars_to_use:
                return str(vars_to_use[var_name])
            return match.group(0)

        return self.VAR_PATTERN.sub(replace_var, content)

    def get_missing_variables(
        self, content: str, variables: dict[str, Any] | None = None
    ) -> list[str]:
        """Get list of variables that are not provided."""
        vars_to_use = {**self.variables, **(variables or {})}
        needed = self.extract_variables(content)
        return [v for v in needed if v not in vars_to_use]


def render_template(
    content: str,
    variables: dict[str, Any] | None = None,
) -> str:
    """Convenience function for template rendering."""
    engine = TemplateEngine()
    return engine.render(content, variables)
