# qrforge

A CLI tool for generating and reading QR codes.

## Installation

```bash
pip install -r requirements.txt
```

Or with pip directly:

```bash
pip install qrcode[pil] pyzbar pillow
```

**System dependency required for `pyzbar`:**
- Linux: `sudo apt-get install libzbar0`
- macOS: `brew install zbar`
- Windows: Usually included with pyzbar wheel

## Usage

### Generate a QR code

```bash
python app.py generate "Your text here" -o output.png
```

Options:
- `-o, --output`: Output file path (default: qrcode.png)
- `-s, --size`: Image size in pixels 1-10000 (default: 300)

### Read a QR code

```bash
python app.py read qrcode.png
```

## Examples

Generate a QR code and save it:
```bash
python app.py generate "https://example.com" -o website.png
```

Read a QR code from an image:
```bash
python app.py read website.png
```

## Error Handling

The tool validates inputs and provides clear error messages:

- Empty text → "Error: Text content cannot be empty"
- Invalid size → "Error: Size must be a positive integer, got X"
- File not found → "Error: File not found: path/to/file.png"
- No QR code → "Error: No QR code found in path/to/file.png"
