"""Configuration management module for Local LLM Chat."""

from dataclasses import asdict, dataclass, fields
from pathlib import Path

import toml


class ConfigError(Exception):
    """Base exception for configuration-related errors."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when the configuration file is not found."""

    pass


class ConfigParseError(ConfigError):
    """Raised when the configuration file cannot be parsed."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration values fail validation."""

    pass


@dataclass
class Config:
    """Configuration dataclass for Local LLM Chat."""

    current_model: str = "llama-3-8b.q4_k_m.gguf"
    model_dir: str = "models"
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = True
    system_prompt: str = "You are a helpful AI assistant."
    use_markdown: bool = True
    syntax_highlighting: bool = True
    show_tokens_per_second: bool = True
    save_dir: str = "conversations"
    auto_save: bool = True
    max_conversations: int = 100

    def __post_init__(self):
        """Validate configuration values after initialization."""
        if self.temperature < 0 or self.temperature > 2.0:
            raise ConfigValidationError(
                f"temperature must be between 0 and 2.0, got {self.temperature}"
            )
        if self.max_tokens <= 0:
            raise ConfigValidationError(f"max_tokens must be positive, got {self.max_tokens}")
        if self.max_conversations <= 0:
            raise ConfigValidationError(
                f"max_conversations must be positive, got {self.max_conversations}"
            )
        if not isinstance(self.stream, bool):
            raise ConfigValidationError(f"stream must be a boolean, got {type(self.stream)}")


def get_default_config() -> Config:
    """Return the default configuration.

    Returns:
        Config: Default configuration with sensible values.
    """
    return Config()


def _parse_toml_file(config_path: str) -> dict:
    """Parse a TOML configuration file.

    Args:
        config_path: Path to the TOML configuration file.

    Returns:
        dict: Parsed TOML data as a dictionary.

    Raises:
        ConfigNotFoundError: If the configuration file does not exist.
        ConfigParseError: If the file cannot be parsed as TOML.
    """
    path = Path(config_path)

    if not path.exists():
        raise ConfigNotFoundError(f"Configuration file not found: {config_path}")

    try:
        return toml.load(path)
    except toml.TomlDecodeError as e:
        raise ConfigParseError(f"Failed to parse TOML file: {e}") from e
    except OSError as e:
        raise ConfigParseError(f"Failed to read configuration file: {e}") from e


def _flatten_config(data: dict) -> dict:
    """Flatten nested TOML config into a single-level dict.

    The TOML config has sections like [default], [display], [history].
    This function flattens them into a single dict.

    Args:
        data: Nested dictionary from TOML parsing.

    Returns:
        dict: Flattened dictionary with all config keys at top level.
    """
    flattened = {}
    for section in data.values():
        if isinstance(section, dict):
            flattened.update(section)
    return flattened


def _config_from_dict(data: dict) -> Config:
    """Create a Config instance from a dictionary.

    Args:
        data: Flattened configuration dictionary.

    Returns:
        Config: Configuration instance.

    Raises:
        ConfigValidationError: If configuration values are invalid.
    """
    config_fields = {f.name for f in fields(Config)}
    filtered_data = {k: v for k, v in data.items() if k in config_fields}

    try:
        return Config(**filtered_data)
    except TypeError as e:
        raise ConfigValidationError(f"Invalid configuration: {e}") from e


def load_config(config_path: str) -> Config:
    """Load configuration from a TOML file.

    If the file is not found, returns the default configuration.
    If the file cannot be parsed, raises a ConfigParseError.

    Args:
        config_path: Path to the TOML configuration file.

    Returns:
        Config: Configuration loaded from file, or default if not found.
    """
    try:
        data = _parse_toml_file(config_path)
        flattened = _flatten_config(data)
        return _config_from_dict(flattened)
    except ConfigNotFoundError:
        # Return default config if file not found
        return get_default_config()


def save_config(config: Config, config_path: str) -> None:
    """Save configuration to a TOML file.

    Args:
        config: Configuration to save.
        config_path: Path to save the TOML configuration file.

    Raises:
        ConfigError: If the configuration cannot be saved.
    """
    # Validate config before saving
    try:
        config = Config(**asdict(config))
    except (TypeError, ValueError) as e:
        raise ConfigValidationError(f"Invalid configuration: {e}") from e

    # Organize config into sections
    config_data = {
        "default": {
            "current_model": config.current_model,
            "model_dir": config.model_dir,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": config.stream,
            "system_prompt": config.system_prompt,
        },
        "display": {
            "use_markdown": config.use_markdown,
            "syntax_highlighting": config.syntax_highlighting,
            "show_tokens_per_second": config.show_tokens_per_second,
        },
        "history": {
            "save_dir": config.save_dir,
            "auto_save": config.auto_save,
            "max_conversations": config.max_conversations,
        },
    }

    path = Path(config_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        toml.dump(config_data, path)
    except OSError as e:
        raise ConfigError(f"Failed to save configuration: {e}") from e
    except toml.TomlEncodeError as e:
        raise ConfigError(f"Failed to encode configuration: {e}") from e
