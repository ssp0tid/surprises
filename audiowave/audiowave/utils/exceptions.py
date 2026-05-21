"""Custom exception classes for AudioWave."""


class AudioWaveError(Exception):
    """Base exception for all AudioWave errors."""

    pass


class AudioLoadError(AudioWaveError):
    """Raised when audio file cannot be loaded."""

    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(
            f"Cannot load '{filepath}': {reason}. "
            f"Supported formats: MP3, WAV, FLAC, OGG"
        )


class UnsupportedFormatError(AudioLoadError):
    """Raised when audio format is not supported."""

    pass


class CorruptedFileError(AudioLoadError):
    """Raised when audio file appears corrupted."""

    pass


class FileAccessError(AudioLoadError):
    """Raised when file cannot be accessed."""

    pass


class AudioAnalysisError(AudioWaveError):
    """Raised when audio analysis fails."""

    pass


class InsufficientDataError(AudioAnalysisError):
    """Raised when there is not enough audio data for analysis."""

    pass


class VisualizationError(AudioWaveError):
    """Raised when visualization generation fails."""

    pass


class RenderError(VisualizationError):
    """Raised when rendering fails."""

    pass


class ExportError(VisualizationError):
    """Raised when export fails."""

    pass


class ConfigurationError(AudioWaveError):
    """Raised when configuration is invalid."""

    pass


class ConfigFileError(ConfigurationError):
    """Raised when config file cannot be loaded."""

    pass


class InvalidOptionError(ConfigurationError):
    """Raised when an invalid option is provided."""

    pass


class CLIError(AudioWaveError):
    """Raised when CLI operation fails."""

    pass


class InvalidArgumentError(CLIError):
    """Raised when invalid arguments are provided."""

    pass


class CommandExecutionError(CLIError):
    """Raised when command execution fails."""

    pass
