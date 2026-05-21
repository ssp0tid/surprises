"""Main CLI application with Typer."""

import typer
from pathlib import Path
from typing import Optional

from code_sentinel.config import load_config
from code_sentinel.logging import configure_logging
from code_sentinel.engine import LlamaEngine
from code_sentinel.analyzer import ReviewAnalyzer

app = typer.Typer(
    name="code-sentinel",
    help="AI-powered local code review assistant",
    add_completion=False,
)


@app.command()
def review(
    path: str = typer.Argument(..., help="Path to file or directory to review"),
    focus: Optional[str] = typer.Option(
        None, "--focus", "-f", help="Review focus: security, bugs, patterns, all"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="GGUF model path"),
    format: str = typer.Option("text", "--format", help="Output: text, json"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
) -> None:
    """Review code for issues and improvements."""
    configure_logging(verbose)
    cfg = load_config(config)

    # Initialize engine
    try:
        engine = LlamaEngine(model_path=model or cfg.default_model)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("Hint: Use --model to specify a valid model path", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error loading model: {e}", err=True)
        raise typer.Exit(1)

    # Run analysis
    analyzer = ReviewAnalyzer(engine, focus=focus or cfg.focus)
    results = analyzer.analyze_path(Path(path))

    # Output
    if format == "json":
        import json

        print(
            json.dumps(
                [
                    {"issue": f.issue, "severity": f.severity, "line": f.line}
                    for f in results.findings
                ],
                indent=2,
            )
        )
    else:
        for f in results.findings:
            print(f"[{f.severity}] {f.file}:{f.line} - {f.issue}")
            if f.fix:
                print(f"  Fix: {f.fix}")
        print(
            f"\nReviewed {results.files_reviewed} files in {results.duration_seconds:.2f}s"
        )


@app.command()
def models() -> None:
    """List available models."""
    from code_sentinel.config import get_model_list

    for model in get_model_list():
        typer.echo(f"  {model}")


@app.command(name="config")
def config_cmd(
    show: bool = typer.Option(False, "--show", help="Show config"),
) -> None:
    """Manage configuration."""
    if show:
        cfg = load_config()
        typer.echo(f"default_model: {cfg.default_model}")
        typer.echo(f"focus: {cfg.focus}")
        typer.echo(f"temperature: {cfg.temperature}")
