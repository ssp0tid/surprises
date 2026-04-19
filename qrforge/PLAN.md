# QRForge Plan - Terminal QR Code Generator/Reader

## Project Overview

- **Project Name**: QRForge
- **Type**: CLI Tool (Python)
- **Core Functionality**: Generate QR codes from text/URLs, save as PNG/SVG; read QR codes from image files
- **Target Users**: Developers, terminal power users, sysadmins needing quick QR operations

## Technical Stack

- **Language**: Python 3.10+
- **QR Generation**: `qrcode` library (with `pillow` for PNG, `svglib` for SVG)
- **QR Reading**: `opencv-python` or `pyzbar` (with `zbar` system dependency)
- **CLI Framework**: `argparse` (stdlib) or `click`
- **Output Formats**: PNG, SVG

## CLI Interface

```bash
qrforge [OPTIONS] COMMAND [ARGS]

Options:
  --help  Show help and exit

Commands:
  generate    Generate QR code from text/URL
  read        Read QR code from image file
  list        List saved QR codes
```

### Subcommand: generate

```bash
qrforge generate TEXT [OPTIONS]

Arguments:
  TEXT                    Text or URL to encode

Options:
  -o, --output PATH      Output file path (default: ./qrcode.png)
  -f, --format FORMAT   Output format: png, svg (default: png)
  -s, --size INTEGER    QR code size/box size (default: 10)
  --fill-color COLOR    QR code fill color (default: black)
  --back-color COLOR    Background color (default: white)
  --error-correction    Error correction level: L, M, Q, H (default: M)
```

### Subcommand: read

```bash
qrforge read IMAGE_PATH [OPTIONS]

Arguments:
  IMAGE_PATH             Path to image file containing QR code

Options:
  -o, --output PATH      Output file to save decoded text (optional)
  -v, --verbose         Print additional info (confidence, version)
```

### Subcommand: list

```bash
qrforge list [OPTIONS]

Options:
  -d, --directory PATH  Directory to list QR codes from (default: .)
  -f, --filter FORMAT   Filter by format: png, svg, all (default: all)
```

## Project Structure

```
qrforge/
├── qrforge/
│   ├── __init__.py
│   ├── cli.py           # Main CLI entry point
│   ├── generator.py     # QR code generation logic
│   ├── reader.py        # QR code reading logic
│   ├── config.py        # Configuration and defaults
│   └── utils.py         # Utility functions
├── tests/
│   ├── test_generator.py
│   ├── test_reader.py
│   └── test_cli.py
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Lock file (if using uv)
├── README.md
└── PLAN.md              # This file
```

## Core Functions

### `generator.py`

```python
def generate_qr(
    data: str,
    output_path: str,
    format: str = "png",
    box_size: int = 10,
    fill_color: str = "black",
    back_color: str = "white",
    error_correction: str = "M"
) -> None:
    """Generate QR code and save to file."""

def validate_data(data: str) -> bool:
    """Validate input data for QR encoding."""
```

### `reader.py`

```python
def read_qr(image_path: str) -> dict:
    """
    Read QR code from image file.
    Returns: { "data": str, "version": int, "confidence": float }
    """
```

### `cli.py`

- `argparse` with subparsers for each command
- Proper help messages and usage examples
- Error handling with user-friendly messages

## Dependencies

```toml
[project]
name = "qrforge"
version = "0.1.0"
description = "Terminal QR code generator/reader"
requires-python = ">=3.10"

dependencies = [
    "qrcode[pil]>=7.4.2",
    "opencv-python>=4.8.0",
    "pyzbar>=0.1.9",
]
```

**System Dependencies**:
- `zbar` (system library for pyzbar)

## Implementation Phases

### Phase 1: Setup
- Initialize project with pyproject.toml
- Create basic project structure
- Install dependencies

### Phase 2: Generator
- Implement `generator.py`
- Support PNG and SVG output
- Add color customization
- Error correction levels

### Phase 3: Reader
- Implement `reader.py` using pyzbar
- Handle multiple QR codes in one image
- Add confidence/size info output

### Phase 4: CLI
- Implement `cli.py` with argparse
- Add subcommands: generate, read, list
- Proper error handling and help

### Phase 5: Testing
- Unit tests for generator and reader
- CLI integration tests
- Edge case handling

## Acceptance Criteria

1. ✅ `qrforge generate "https://example.com" -o qr.png` creates valid PNG QR
2. ✅ `qrforge generate "hello" -f svg -o qr.svg` creates valid SVG QR
3. ✅ `qrforge read qr.png` outputs decoded text
4. ✅ `qrforge list` shows QR files in directory
5. ✅ All commands have `--help` documentation
6. ✅ Errors are handled gracefully with clear messages

## Future Enhancements (Out of Scope)

- GUI mode
- QR batch processing
- Custom logo embedding
- QR style variations (rounded corners, colors)