"""QR code parsing for otpauth:// URIs."""

import os
from urllib.parse import unquote, parse_qs

from PIL import Image

try:
    from pyzbar import pyzbar

    HAS_PYZBAR = True
except ImportError:
    HAS_PYZBAR = False

from totpauth.exceptions import QRDecodeError, InvalidOtpAuthURLError


SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg"}


def parse_qr_file(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise QRDecodeError(image_path)
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise QRDecodeError(image_path)
    img = Image.open(image_path)
    if img.mode != "L":
        img = img.convert("L")
    decoded = _decode_qr(img)
    if not decoded:
        raise QRDecodeError(image_path)
    uri = decoded[0]
    if not uri.startswith("otpauth://"):
        raise InvalidOtpAuthURLError(uri)
    return uri


def _decode_qr(img: Image.Image):
    if HAS_PYZBAR:
        try:
            result = pyzbar.decode(img)
            if result:
                return [r.data.decode("utf-8") for r in result]
        except Exception as e:
            import sys

            print(f"Warning: QR decoding failed: {e}", file=sys.stderr)
    return None


def parse_otpauth_uri(uri: str) -> dict:
    if not uri.startswith("otpauth://"):
        raise InvalidOtpAuthURLError(uri)
    uri = uri[8:]
    if "//" in uri:
        uri = uri.replace("//", "/", 1)
    parts = uri.split("?")
    path_parts = parts[0].split("/")
    otp_type = path_parts[0] if path_parts else "totp"
    label = "/".join(path_parts[1:]) if len(path_parts) > 1 else ""
    if not label:
        raise InvalidOtpAuthURLError(uri)
    label = unquote(label)
    if ":" in label:
        issuer, account_name = label.split(":", 1)
    else:
        issuer = label
        account_name = ""
    params = {}
    if len(parts) > 1:
        for key, value in parse_qs(parts[1]).items():
            params[key] = value[0] if value else ""
    secret = params.get("secret", "")
    if not secret:
        raise InvalidOtpAuthURLError(uri)
    algorithm = params.get("algorithm", "SHA1").upper()
    digits = int(params.get("digits", "6"))
    period = int(params.get("period", "30"))
    counter = int(params.get("counter", "0"))
    if not issuer and params.get("issuer"):
        issuer = params.get("issuer")
    return {
        "issuer": issuer,
        "account_name": account_name,
        "secret": secret,
        "otp_type": otp_type,
        "algorithm": algorithm,
        "digits": digits,
        "period": period,
        "counter": counter,
    }
