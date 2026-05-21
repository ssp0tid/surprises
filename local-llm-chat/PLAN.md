# Local LLM Chat CLI - Implementation Plan

## Context
- **Project**: CLI tool to chat with local LLMs (llama.cpp compatible)
- **Features**: Markdown rendering, conversation history, system prompts, model switching
- **State**: Empty directory - new project

---

## Technical Decisions

| Component | Library | Version | Rationale |
|-----------|---------|---------|----------|
| LLM Inference | `llama-cpp-python` | `>=0.2.0` | GGUF models, chat templates, streaming, OpenAI-compatible API |
| CLI Framework | `click` + `rich-click` | `click>=8.0`, `rich-click>=1.9` | Rich help output, subcommands, type validation |
| Markdown Rendering | `rich` | `>=13.0` | Tables, code blocks, syntax highlighting, links |
| Model Management | `gguf` | `>=0.10` | GGUF metadata parsing (quantization type, context size) |
| Config Management | `toml` | `>=0.10` | Human-readable, validated, typed |
| Chat Templates | `jinja2` | `>=3.0` | Built-in llama.cpp template support |

---

## File Structure

```
local-llm-chat/
├── pyproject.toml                 # Project metadata + dependencies
├── README.md                      # Quick start guide
├── src/
│   └── local_llm_chat/
│       ├── __init__.py           # __version__ = "0.1.0"
│       ├── __main__.py           # Click entry point
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py          # Main CLI group (click)
│       │   ├── chat.py          # chat subcommand
│       │   ├── model.py         # model subcommand (list, switch)
│       │   ├── config.py        # config subcommand
│       │   └── history.py       # history subcommand
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py        # llama-cpp-python wrapper
│       │   ├── prompt.py       # System prompt + template handling
│       │   └── renderer.py     # Markdown -> Rich rendering
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── conversation.py # Conversation CRUD
│       │   └── config.py        # Config read/write (toml)
│       ├── models/
│       │   ├── __init__.py
│       │   └── registry.py      # Model registry (scan, list, switch)
│       └── utils/
│           ├── __init__.py
│           ├── pretty.py        # Status indicators, spinner
│           └── io.py           # Terminal input with rich prompt
├── models/                       # GGUF model Storage (user-managed)
├── conversations/              # Saved conversations (JSON)
├── config.toml                  # Global configuration
└── .gitignore                   # Ignore: models/, *.gguf, __pycache__/, *.pyc
```

---

## Dependencies

### Core (Required)

```toml
dependencies = [
    "click>=8.0.0",
    "rich-click>=1.9.0",
    "rich>=13.0.0",
    "llama-cpp-python>=0.2.0",
    " gguf>=0.10.0",
    "toml>=0.10.0",
    "jinja2>=3.0.0",
]
```

### Dev (Required)

```toml
dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

### Optional

```toml
dependencies = [
    "pillow>=10.0; extra == 'images'",   # Image generation support
]
```

---

## API Design

### CLI Commands

```
local-llm-chat --help
local-llm-chat chat --help
local-llm-chat model --help
local-llm-chat config --help
local-llm-chat history --help
```

#### `main.py` (Entry Point)

```python
@click.group()
@click.version_option()
@click.option("--config", "-c", "config_path", type=click.Path(), default="config.toml")
@click.pass_context
def main(ctx, config_path):
    """Chat with local LLMs directly from your terminal."""
    ctx.ensure_object(Config)
    ctx.obj["config"] = load_config(config_path)
```

#### `chat.py` (Core Chat)

```python
@main.group()
def chat():
    """Chat with loaded model."""
    pass

@chat.command()
@click.option("--model", "-m", "model", type=str, default=None)
@click.option("--system", "-s", "system_prompt", type=str, default=None)
@click.option("--conversation", "-c", "conversation_id", type=str, default=None)
@click.option("--stream/--no-stream", "stream", default=True)
@click.pass_context
def start(ctx, model, system_prompt, conversation_id, stream):
    """Start an interactive chat session."""
    # Model loading, template setup, conversation restoration
```

#### `model.py` (Model Management)

```python
@main.group()
def model():
    """Manage local models."""
    pass

@model.command("list")
def model_list():
    """List available models."""
    # Scan models/, show metadata (name, size, quantization)

@model.command("switch")
@click.argument("model_name")
def model_switch(model_name):
    """Switch to a different model (within chat or standalone)."""

@model.command("info")
@click.argument("model_name")
def model_info(model_name):
    """Show model metadata (size, quantization, context size)."""
```

#### `config.py` (Configuration)

```python
@main.group()
def config():
    """Manage configuration."""
    pass

@config.command("show")
def config_show():
    """Display current configuration."""

@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Update configuration value."""
```

#### `history.py` (Conversation History)

```python
@main.group()
def history():
    """Manage conversation history."""
    pass

@history.command("list")
def history_list():
    """Show all saved conversations."""

@history.command("load")
@click.argument("conversation_id")
def history_load(conversation_id):
    """Load a conversation into chat."""

@history.command("delete")
@click.argument("conversation_id")
def history_delete(conversation_id):
    """Delete a conversation."""
```

---

## Data Flows

### Chat Flow

```
User Input
    │
    ▼
┌──────────────────────────────────────────┐
│ Input: Render rich prompt (system, model)│
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ PromptBuilder: Build chat template        │
│ - System prompt (conversation or default)│
│ - Conversation history (message list)    │
│ - User message                           │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ LLMEngine: Generate response              │
│ - llama_cpp.Llama                     │
│ - Stream token-by-token                 │
│ - Apply chat template                   │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ Renderer: Markdown → Rich                │
│ - Parse markdown (Rich library)          │
│ - Render tables, code blocks, links     │
│ - Syntax highlighting for code         │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ Storage: Auto-save conversation         │
│ - Append message to conversation       │
│ - Persist to JSON                       │
└──────────────────────────────────────────┘
```

### Model Switching Flow

```
/model switch <name>
    │
    ▼
Check: models/<name>.gguf exists?
    │
    ├─No─→ Error: "Model not found at models/<name>.gguf"
    │
    ▼Yes
Check: Can load with llama-cpp-python?
    │
    ├─Fail─→ Error: "Failed to load model: <details>"
    │
    ▼Yes
Update: config.toml (current_model)
    │
    ▼
Display: "Switched to <name>" (confirm)
```

---

## Error Handling

### Error Categories

| Category | Error Type | Handling |
|----------|-----------|----------|
| Model Loading | `ModelNotFoundError` | List available models, suggest path |
| | `ModelLoadFailedError` | Show llama.cpp error, suggest GGUF validation |
| | `InvalidGGUFError` | Show GGUF metadata parsing failure |
| Generation | `GenerationError` | Stream error, suggest retry |
| | `ContextOverflowError` | Truncate history + system prompt |
| Storage | `ConfigReadError` | Show config path, suggest defaults |
| | `ConversationLoadError` | Show corrupted JSON details |
| Display | `TerminalTooSmallError` | Shrink output or suggest resize |
| | `UnicodeError` | Fallback to ASCII rendering |

### Error Response Format

```python
# Console error (rich)
[red]Error:[/red] <message>
[dim]Hint:[/dim] <suggestion>

# Programmatic error (JSON)
{
    "error": "ModelNotFoundError",
    "message": "Model 'llama-3-8b.q4_k_m.gguf' not found",
    "hint": "Run 'local-llm-chat model list' to see available models",
    "model_path": "models/llama-3-8b.q4_k_m.gguf"
}
```

### Retry Logic

```python
# Automatic retry with exponential backoff
for attempt in range(3):
    try:
        response = engine.generate(prompt)
        break
    except GenerationError as e:
        if attempt < 2:
            warn(f"Retry {attempt + 1}/3 in {2 ** attempt}s...")
            sleep(2 ** attempt)
        else:
            raise
```

---

## Edge Cases

### Large Responses

| Issue | Handling |
|-------|----------|
| >10k tokens | Stream + progress indicator |
| >terminal height | Paginate (scroll or chunk) |
| Slow generation | Show tokens/sec, ETA |

### Model Issues

| Issue | Handling |
|-------|----------|
| No models found | Show onboarding (download, place in models/) |
| Corrupted GGUF | Validate with `gguf` library, show error details |
| Out of VRAM | Suggest quantization downgrade, close other models |

### Session Issues

| Issue | Handling |
|-------|----------|
| Interrupted (Ctrl+C) | Auto-save conversation, confirm on next start |
| Corrupted history | Show partial load + offer to delete |
| Large conversation | Lazy-load messages, paginate history list |

### Terminal Issues

| Issue | Handling |
|-------|----------|
| Non-TTY stdin | Use file input or --message flag |
| Small terminal | Reduce font size or disable markdown |
| Unicode not supported | ASCII fallback |

### Prompt Issues

| Issue | Handling |
|-------|----------|
| System prompt too long | Truncate + warn |
| No system prompt | Use default from config |
| Template mismatch | Auto-detect or show template options |

---

## Implementation Order

### Phase 1 - Core (Week 1)

1. **Project Setup**
   - Initialize pyproject.toml
   - Create directory structure
   - Basic imports + \__version__

2. **Configuration**
   - Config toml read/write
   - Model registry (scan models/)
   - GGUF metadata parsing

3. **LLM Engine**
   - llama-cpp-python wrapper
   - Basic generation (non-streaming)
   - Chat template (Jinja2)

### Phase 2 - CLI (Week 2)

4. **CLI Framework**
   - Main click group
   - Rich help output
   - Global --config option

5. **Chat Command**
   - Interactive input
   - Streaming output
   - Basic markdown rendering

6. **Model Commands**
   - model list
   - model info

### Phase 3 - Features (Week 3)

7. **Conversation History**
   - JSON storage
   - Load/save conversations
   - Chat history integration

8. **System Prompts**
   - System prompt management
   - Per-conversation system prompts

9. **Model Switching**
   - model switch
   - In-chat switching (/switch command)

### Phase 4 - Polish (Week 4)

10. **Markdown Rendering**
    - Tables, code blocks
    - Syntax highlighting
    - Link handling

11. **Error Handling**
    - All error types
    - Retry logic
    - User hints

12. **Testing + Docs**
    - Basic pytest coverage
    - README.md

---

## Configuration Schema

### config.toml

```toml
[default]
# Model settings
current_model = "llama-3-8b.q4_k_m.gguf"
model_dir = "models"              # Relative to project or absolute path

# Generation settings
temperature = 0.7
max_tokens = 2048
stream = true

# System prompt
system_prompt = "You are a helpful AI assistant."

[display]
# Terminal settings
use_markdown = true
syntax_highlighting = true
show_tokens_per_second = true

[history]
# Conversation storage
save_dir = "conversations"
auto_save = true
max_conversations = 100
```

---

## Conversation Schema

### conversations/{id}.json

```json
{
  "id": "conv_20250601_143022",
  "model": "llama-3-8b.q4_k_m.gguf",
  "system_prompt": "You are a helpful coding assistant.",
  "created_at": "2025-06-01T14:30:22Z",
  "updated_at": "2025-06-01T14:35:45Z",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful coding assistant."
    },
    {
      "role": "user",
      "content": "Explain threading in Python."
    },
    {
      "role": "assistant",
      "content": "Threading in Python allows..."
    }
  ]
}
```

---

## Key Design Decisions

1. **Model Storage**: User-managed `models/` directory (no auto-download)
   - Rationale: Keeps CLI simple, respects disk space, avoids piracy concerns

2. **Config Format**: TOML (not YAML)
   - Rationale: Structured parsing, less error-prone, Python native

3. **Markdown**: Rich library (not mistune)
   - Rationale: Rich handles terminal rendering + markdown parsing

4. **Storage**: JSON (not SQLite)
   - Rationale: Human-readable, versionable, no dependency

5. **Templates**: Jinja2 (built-in llama.cpp)
   - Rationale: Standard, supports all templates, well-tested