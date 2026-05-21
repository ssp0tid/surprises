# Local LLM Chat

CLI tool to chat with local LLM models (llama.cpp compatible).

## Installation

```bash
pip install -e .
```

This installs the `local-llm-chat` command-line tool in editable mode.

## Model Download Instructions

This tool works with GGUF format models compatible with [llama.cpp](https://github.com/ggerganov/llama.cpp).

### Recommended Models

| Model | Size | Description |
|-------|------|-------------|
| Llama 3.1 8B | ~5GB | Good balance of quality and speed |
| Phi 3 Mini | ~2.5GB | Smaller, faster, good for testing |
| Qwen 2.5 7B | ~5GB | Strong multilingual performance |

### Downloading Models

**Using Hugging Face (recommended):**

```bash
# Example: Download Llama 3.1 8B Instruct (Q4_K_M quantization)
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct-GGUF --include "*Q4_K_M.gguf" --local-dir ./models
```

Or browse [GGUF models on Hugging Face](https://huggingface.co/models?search=gguf) and download manually.

**Using Ollama (export to GGUF):**

```bash
# Pull a model and export
ollama pull llama3
ollama show llama3 --modelfile

# Export using llama.cpp (see llama.cpp docs for conversion)
```

Place your `.gguf` model files in the `models/` directory (or configure a custom path).

## Basic Usage Examples

### Start a Chat Session

```bash
local-llm-chat chat start
```

This starts an interactive chat. Type your message and press Enter. Type `/quit` to exit.

### List Available Models

```bash
local-llm-chat model list
```

Shows all GGUF models in your models directory with quantization, size, and context info.

### Switch to a Different Model

```bash
local-llm-chat model switch llama-3.1-8b.q4_k_m.gguf
```

### View Model Information

```bash
local-llm-chat model info llama-3.1-8b.q4_k_m.gguf
```

Shows detailed info (size, quantization, context length) for a specific model.

### Resume a Previous Conversation

```bash
local-llm-chat chat start --conversation <conversation-id>
```

### Command-Line Options

```bash
# Use a specific model (overrides config)
local-llm-chat chat start -m llama-3.1-8b.q4_k_m.gguf

# Use a custom system prompt
local-llm-chat chat start -s "You are a helpful coding assistant."

# Disable streaming
local-llm-chat chat start --no-stream

# Use a custom config file
local-llm-chat -c path/to/config.toml chat start
```

## Configuration Options

Configuration is stored in `config.toml` in your project directory.

### Default Configuration File

```toml
[default]
# Model to use (filename from model_dir)
current_model = "llama-3-8b.q4_k_m.gguf"

# Directory containing model files
model_dir = "models"

# LLM parameters
temperature = 0.7
max_tokens = 2048
stream = true
system_prompt = "You are a helpful AI assistant."

[display]
# Output formatting
use_markdown = true
syntax_highlighting = true
show_tokens_per_second = true

[history]
# Conversation storage
save_dir = "conversations"
auto_save = true
max_conversations = 100
```

### Configuration Options Reference

| Section | Option | Type | Default | Description |
|---------|--------|------|---------|-------------|
| default | `current_model` | string | `"llama-3-8b.q4_k_m.gguf"` | Active model filename |
| default | `model_dir` | string | `"models"` | Directory containing GGUF models |
| default | `temperature` | float | `0.7` | Sampling temperature (0.0-2.0) |
| default | `max_tokens` | int | `2048` | Maximum tokens to generate |
| default | `stream` | bool | `true` | Enable streaming responses |
| default | `system_prompt` | string | `"You are a helpful AI assistant."` | System prompt |
| display | `use_markdown` | bool | `true` | Render markdown in responses |
| display | `syntax_highlighting` | bool | `true` | Enable code syntax highlighting |
| display | `show_tokens_per_second` | bool | `true` | Show generation speed |
| history | `save_dir` | string | `"conversations"` | Directory for saved conversations |
| history | `auto_save` | bool | `true` | Auto-save conversations after each response |
| history | `max_conversations` | int | `100` | Maximum conversations to keep |

### Creating a Custom Configuration

Create a `config.toml` file in your project directory:

```toml
[default]
current_model = "phi-3-mini-q4_k_m.gguf"
model_dir = "./models"
temperature = 0.8
max_tokens = 1024
stream = false
system_prompt = "You are a concise and helpful assistant."

[display]
use_markdown = true
syntax_highlighting = true
show_tokens_per_second = false

[history]
save_dir = "./conversations"
auto_save = true
max_conversations = 50
```

## Requirements

- Python 3.10+
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) (installed automatically)

## License

MIT