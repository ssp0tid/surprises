#!/usr/bin/env python3
"""qrforge - QR code generation and decoding CLI tool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode


class QRForgeError(Exception):
    """Base exception for QRForge errors."""

    pass


class QRGenerationError(QRForgeError):
    """Raised when QR code generation fails."""

    pass


class QRReadError(QRForgeError):
    """Raised when QR code reading fails."""

    pass


def validate_size(size: int) -> int:
    """Validate and return a valid image size.

    Args:
        size: Requested image size in pixels.

    Returns:
        Validated size value.

    Raises:
        QRForgeError: If size is invalid.
    """
    if size <= 0:
        raise QRForgeError(f"Size must be a positive integer, got {size}")
    if size > 10000:
        raise QRForgeError(f"Size too large (max 10000px), got {size}")
    return size


def validate_text(text: str) -> str:
    """Validate and return text content.

    Args:
        text: Text to encode.

    Returns:
        Validated text.

    Raises:
        QRForgeError: If text is empty.
    """
    if not text or not text.strip():
        raise QRForgeError("Text content cannot be empty")
    return text.strip()


def generate_qr(text: str, output: Path, size: int = 300) -> None:
    """Generate a QR code from text and save as PNG.

    Args:
        text: The text/content to encode in the QR code.
        output: Path where the PNG file will be saved.
        size: Size of the QR code image in pixels (default: 300).

    Raises:
        QRGenerationError: If generation or saving fails.
    """
    # Validate inputs
    text = validate_text(text)
    size = validate_size(size)

    # Ensure output directory exists
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise QRGenerationError(f"Cannot create output directory: {e}")

    # Generate QR code
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    except Exception as e:
        raise QRGenerationError(f"Failed to generate QR code: {e}")

    # Save image
    try:
        img.save(output)
        print(f"QR code saved to {output}")
    except PermissionError as e:
        raise QRGenerationError(f"Permission denied writing to {output}: {e}")
    except OSError as e:
        raise QRGenerationError(f"Failed to save image to {output}: {e}")


def read_qr(image_path: Path) -> str:
    """Read and decode a QR code from a PNG image.

    Args:
        image_path: Path to the PNG image containing a QR code.

    Returns:
        The decoded text content from the QR code.

    Raises:
        QRReadError: If file not found, cannot be opened, or contains no QR code.
    """
    # Check file exists
    if not image_path.exists():
        raise QRReadError(f"File not found: {image_path}")
    if not image_path.is_file():
        raise QRReadError(f"Path is not a file: {image_path}")

    # Open and decode image
    try:
        img = Image.open(image_path)
    except PermissionError:
        raise QRReadError(f"Permission denied reading {image_path}")
    except Exception:
        raise QRReadError(f"Cannot open image: {image_path}")

    # Try to decode
    try:
        decoded_objects = decode(img)
    except Exception as e:
        raise QRReadError(f"Failed to decode image: {e}")

    if not decoded_objects:
        raise QRReadError(f"No QR code found in {image_path}")

    try:
        return decoded_objects[0].data.decode("utf-8")
    except UnicodeDecodeError:
        raise QRReadError("QR code contains invalid UTF-8 data")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="qrforge",
        description="QR code generation and decoding CLI tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a QR code from text",
    )
    generate_parser.add_argument(
        "text",
        help="Text or content to encode in the QR code",
    )
    generate_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("qrcode.png"),
        help="Output PNG file path (default: qrcode.png)",
    )
    generate_parser.add_argument(
        "-s",
        "--size",
        type=int,
        default=300,
        help="Image size in pixels (default: 300, max: 10000)",
    )

    read_parser = subparsers.add_parser(
        "read",
        help="Read a QR code from a PNG image",
    )
    read_parser.add_argument(
        "image",
        type=Path,
        help="Path to the PNG image containing a QR code",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        try:
            generate_qr(args.text, args.output, args.size)
        except QRForgeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "read":
        try:
            result = read_qr(args.image)
            print(result)
        except QRForgeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
