"""Configuration management with pydantic."""

from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib


@dataclass
class Config:
    """Configuration for CodeSentinel."""

    # Model settings
    default_model: str = "codellama-7b-instruct.q4_k_m.gguf"
    model_dir: str = "models"
    n_ctx: int = 4096
    n_gpu_layers: int = 0

    # Review settings
    focus: str = "all"
    severity_threshold: str = "low"
    max_issues: int = 50
    temperature: float = 0.2


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file."""
    if config_path is None:
        config_path = Path("config.toml")

    if not config_path.exists():
        return Config()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return Config(**data.get("code_sentinel", {}))


def get_model_list(model_dir: str | None = None) -> list[str]:
    """List available models in model_dir."""
    if model_dir is None:
        cfg = load_config()
        model_dir = cfg.model_dir
    models_path = Path(model_dir)
    if not models_path.exists():
        return []
    return [str(p.name) for p in models_path.glob("*.gguf")]
