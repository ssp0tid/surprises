"""Logging configuration for AudioWave."""

import logging
import sys
from typing import Optional

from audiowave.utils.exceptions import ConfigurationError


DEFAULT_FORMAT = "%(levelname)s: %(message)s"
VERBOSE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(
    verbose: bool = False, quiet: bool = False, log_file: Optional[str] = None
) -> None:
    """Configure logging for AudioWave.

    Args:
        verbose: Enable verbose (DEBUG) logging
        quiet: Suppress INFO messages, show only errors
        log_file: Optional file path for log output
    """
    if verbose and quiet:
        raise ConfigurationError("Cannot use both --verbose and --quiet")

    if verbose:
        level = logging.DEBUG
        format_str = VERBOSE_FORMAT
    elif quiet:
        level = logging.ERROR
        format_str = DEFAULT_FORMAT
    else:
        level = logging.WARNING
        format_str = DEFAULT_FORMAT

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(level=level, format=format_str, handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
