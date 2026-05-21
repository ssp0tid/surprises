"""LLM engine module for interacting with local LLM models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from llama_cpp import ChatCompletionChunk, Llama


class EngineError(Exception):
    """Base exception for engine-related errors."""

    pass


class ModelLoadError(EngineError):
    """Raised when the model cannot be loaded."""

    pass


class InferenceError(EngineError):
    """Raised when inference fails."""

    pass


@dataclass
class GenerationMetrics:
    """Metrics for a generation request."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_eval_time_ms: float
    eval_time_ms: float
    tokens_per_second: Optional[float] = None

    def __post_init__(self):
        """Calculate tokens per second."""
        if self.eval_time_ms > 0:
            self.tokens_per_second = self.completion_tokens / (self.eval_time_ms / 1000)


class LLMEngine:
    """Engine for interacting with local LLM models via llama.cpp."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = 0,
        n_threads: Optional[int] = None,
        n_batch: int = 512,
        verbose: bool = False,
    ) -> None:
        """Initialize the LLM engine.

        Args:
            model_path: Path to the GGUF model file.
            n_ctx: Context window size.
            n_gpu_layers: Number of layers to offload to GPU.
            n_threads: Number of CPU threads to use.
            n_batch: Maximum batch size for prompt evaluation.
            verbose: Enable verbose logging.

        Raises:
            ModelLoadError: If the model cannot be loaded.
        """
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._llm: Optional[Llama] = None
        self._load_model(
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            n_batch=n_batch,
            verbose=verbose,
        )

    def _load_model(
        self,
        n_ctx: int,
        n_gpu_layers: int,
        n_threads: Optional[int],
        n_batch: int,
        verbose: bool,
    ) -> None:
        """Load the LLM model.

        Args:
            n_ctx: Context window size.
            n_gpu_layers: Number of layers to offload to GPU.
            n_threads: Number of CPU threads to use.
            n_batch: Maximum batch size for prompt evaluation.
            verbose: Enable verbose logging.

        Raises:
            ModelLoadError: If the model cannot be loaded.
        """
        path = Path(self._model_path)
        if not path.exists():
            raise ModelLoadError(f"Model file not found: {self._model_path}")

        try:
            self._llm = Llama(
                model_path=str(path),
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_threads=n_threads,
                n_batch=n_batch,
                verbose=verbose,
            )
        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {e}") from e

    @property
    def model_path(self) -> str:
        """Return the model path."""
        return self._model_path

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[list[str]] = None,
        stream: bool = False,
    ) -> Iterator[ChatCompletionChunk] | str:
        """Generate text from the model.

        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences to stop generation.
            stream: Whether to stream the response.

        Yields:
            ChatCompletionChunk: Streamed response chunks (if stream=True).
            str: Full generated text (if stream=False).

        Raises:
            InferenceError: If generation fails.
        """
        if self._llm is None:
            raise InferenceError("Model not loaded")

        try:
            if stream:
                return self._stream_generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop=stop or [],
                )
            else:
                return self._generate(prompt, temperature, max_tokens, stop or [])
        except Exception as e:
            raise InferenceError(f"Generation failed: {e}") from e

    def _generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: list[str],
    ) -> str:
        """Generate text synchronously.

        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences.

        Returns:
            str: Generated text.
        """
        result = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )
        return result["choices"][0]["text"]

    def _stream_generate(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop: list[str],
    ) -> Iterator[str]:
        """Generate text with streaming.

        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences.

        Yields:
            str: Generated text chunks.
        """
        for chunk in self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        ):
            if chunk.get("choices"):
                text = chunk["choices"][0].get("text")
                if text:
                    yield text

    def get_metrics(self) -> GenerationMetrics:
        """Get last generation metrics.

        Returns:
            GenerationMetrics: Metrics from the last generation.

        Raises:
            InferenceError: If no generation has occurred.
        """
        if self._llm is None:
            raise InferenceError("Model not loaded")

        eval_info = self._llm.get_eval_info()
        return GenerationMetrics(
            prompt_tokens=eval_info["prompt_tokens"],
            completion_tokens=eval_info["completion_tokens"],
            total_tokens=eval_info["total_tokens"],
            prompt_eval_time_ms=eval_info["prompt_eval_time_ms"],
            eval_time_ms=eval_info["eval_time_ms"],
        )

    def close(self) -> None:
        """Close the engine and free resources."""
        if self._llm is not None:
            self._llm.close()
            self._llm = None
