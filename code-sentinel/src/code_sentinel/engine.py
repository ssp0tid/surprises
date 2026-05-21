"""LLM engine wrapper for llama-cpp-python."""

from pathlib import Path

from llama_cpp import Llama


class LlamaEngine:
    """Engine for interacting with local GGUF models."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        n_threads: int | None = None,
        verbose: bool = False,
    ):
        """Initialize the LLM engine.

        Args:
            model_path: Path to GGUF model file.
            n_ctx: Context window size.
            n_gpu_layers: Layers to offload to GPU (0 = CPU only).
            n_threads: CPU threads (None = auto).
            verbose: Enable verbose logging.
        """
        self._model_path = model_path
        self._llm = self._load_model(
            model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            verbose=verbose,
        )

    def _load_model(self, model_path: str, **kwargs) -> Llama:
        """Load the GGUF model."""
        path = Path(model_path)
        if not path.exists():
            # Try model_dir relative path
            path = Path("models") / model_path
            if not path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")

        return Llama(model_path=str(path), **kwargs)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        stop: list[str] | None = None,
    ) -> str:
        """Generate text from the model.

        Args:
            prompt: The prompt to generate from.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences.

        Returns:
            Generated text.
        """
        result = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
        )
        return result["choices"][0]["text"]

    def token_count(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._llm.tokenize(text.encode("utf-8")))

    def close(self) -> None:
        """Close the engine."""
        if self._llm:
            self._llm.close()
