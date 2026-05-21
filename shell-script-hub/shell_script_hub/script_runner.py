"""Script execution engine for shell-script-hub."""

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionResult:
    """Result of script execution."""

    exit_code: int
    output: str
    error: str | None = None
    success: bool = False

    def __post_init__(self):
        self.success = self.exit_code == 0


class ScriptRunner:
    """Executes shell scripts with variable substitution."""

    def __init__(self, shell: str = "/bin/bash"):
        """Initialize runner with shell executable."""
        self.shell = shell

    def execute(
        self,
        content: str,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute script content with variable substitution."""
        from shell_script_hub.templates import TemplateEngine

        engine = TemplateEngine()
        rendered = engine.render(content, variables)

        try:
            result = subprocess.run(
                rendered,
                shell=True,
                executable=self.shell,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return ExecutionResult(
                exit_code=result.returncode,
                output=result.stdout,
                error=result.stderr if result.stderr else None,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=-1,
                output="",
                error="Script execution timed out after 300 seconds",
            )
        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                output="",
                error=str(e),
            )

    def execute_interactive(
        self,
        content: str,
        variables: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute script interactively (for scripts that need user input)."""
        from shell_script_hub.templates import TemplateEngine

        engine = TemplateEngine()
        rendered = engine.render(content, variables)

        try:
            result = subprocess.run(
                rendered,
                shell=True,
                executable=self.shell,
                timeout=300,
            )
            return ExecutionResult(
                exit_code=result.returncode,
                output="",
                error=None,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=-1,
                output="",
                error="Script execution timed out after 300 seconds",
            )
        except Exception as e:
            return ExecutionResult(
                exit_code=-1,
                output="",
                error=str(e),
            )


def serialize_variables(variables: dict[str, Any]) -> str:
    """Serialize variables to JSON string."""
    return json.dumps(variables)


def deserialize_variables(data: str) -> dict[str, Any]:
    """Deserialize variables from JSON string."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}
