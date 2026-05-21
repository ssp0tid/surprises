# CodeSentinel

AI-powered local code review assistant using local LLMs.

## Features

- **Local LLM inference** - Uses llama.cpp/GGUF models for private, offline code review
- **Security analysis** - Detect vulnerabilities, injection, auth issues
- **Bug detection** - Find logic errors, null checks, race conditions
- **Anti-pattern detection** - Identify code smells and maintainability issues
- **Multiple output formats** - Text, JSON output via CLI

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Review a Python file
code-sentinel review src/auth.py

# Security-focused review
code-sentinel review src/auth.py --focus security

# JSON output
code-sentinel review src/auth.py --format json

# Custom model
code-sentinel review src/auth.py --model models/codellama-7b.gguf

# Show config
code-sentinel config --show
```

## Requirements

- Python 3.11+
- GGUF model (e.g., CodeLlama, Starcoder)

## Configuration

Create `config.toml`:

```toml
[code_sentinel]
default_model = "codellama-7b-instruct.q4_k_m.gguf"
model_dir = "models"
n_ctx = 4096
focus = "all"
temperature = 0.2
```

## License

MIT
