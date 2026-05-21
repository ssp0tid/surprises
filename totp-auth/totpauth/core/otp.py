"""OTP generation using pyotp."""

import pyotp


def generate_totp(
    secret: str, digits: int = 6, period: int = 30, algorithm: str = "SHA1"
) -> str:
    totp = pyotp.TOTP(secret, digits=digits, interval=period, digest=algorithm.lower())
    return totp.now()


def generate_hotp(
    secret: str, counter: int, digits: int = 6, algorithm: str = "SHA1"
) -> str:
    hotp = pyotp.HOTP(secret, digits=digits, digest=algorithm.lower())
    return hotp.at(counter)


def verify_totp(
    secret: str, code: str, digits: int = 6, period: int = 30, algorithm: str = "SHA1"
) -> bool:
    totp = pyotp.TOTP(secret, digits=digits, interval=period, digest=algorithm.lower())
    return totp.verify(code)


def verify_hotp(
    secret: str, code: str, counter: int, digits: int = 6, algorithm: str = "SHA1"
) -> bool:
    hotp = pyotp.HOTP(secret, digits=digits, digest=algorithm.lower())
    return hotp.verify(code, counter)
