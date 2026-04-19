import os
import secrets
from datetime import datetime, timedelta
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

PASTES = {}

SALT_LENGTH = 32
NONCE_LENGTH = 12
KEY_LENGTH = 32


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=600000,
    )
    return kdf.derive(password.encode())


def encrypt_content(content: str, password: str = None) -> tuple[bytes, bytes, bytes]:
    salt = os.urandom(SALT_LENGTH)
    nonce = os.urandom(NONCE_LENGTH)

    if password:
        key = derive_key(password, salt)
    else:
        key = salt

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, content.encode("utf-8"), None)

    return ciphertext, nonce, salt


def decrypt_content(
    ciphertext: bytes, nonce: bytes, salt: bytes, password: str = None
) -> str:
    if password:
        key = derive_key(password, salt)
    else:
        key = salt

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def generate_paste_id() -> str:
    return secrets.token_urlsafe(12)


def get_verified_password(paste_id: str) -> str | None:
    return session.get(f"paste_verified_{paste_id}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create", methods=["POST"])
def create():
    content = request.form.get("content", "").strip()
    if not content:
        flash("Content cannot be empty", "error")
        return redirect(url_for("index"))

    password = request.form.get("password", "").strip() or None
    expiration = request.form.get("expiration", "1h")
    burn_after_reading = request.form.get("burn_after_reading") == "on"

    # Encrypt content
    ciphertext, nonce, salt = encrypt_content(content, password)

    # Determine expiration
    expires_at = None
    if expiration == "1h":
        expires_at = datetime.now() + timedelta(hours=1)
    elif expiration == "1d":
        expires_at = datetime.now() + timedelta(days=1)
    # 'forever' means no expiration

    paste_id = generate_paste_id()

    PASTES[paste_id] = {
        "ciphertext": ciphertext,
        "nonce": nonce,
        "salt": salt,
        "has_password": bool(password),
        "burn_after_reading": burn_after_reading,
        "expires_at": expires_at,
        "created_at": datetime.now(),
    }

    # Build URL based on whether password is set
    view_url = url_for("view", paste_id=paste_id, _external=True)
    if password:
        view_url += f"?password=1"

    return render_template(
        "created.html",
        paste_id=paste_id,
        view_url=view_url,
        has_password=bool(password),
    )


@app.route("/view/<paste_id>")
def view(paste_id):
    paste = PASTES.get(paste_id)
    if not paste:
        abort(404)

    # Check expiration
    if paste["expires_at"] and datetime.now() > paste["expires_at"]:
        del PASTES[paste_id]
        flash("This paste has expired", "error")
        return redirect(url_for("index"))

    # Check if password required
    needs_password = paste["has_password"]
    password = get_verified_password(paste_id)

    if needs_password and not password:
        return render_template("password_prompt.html", paste_id=paste_id)

    # Decrypt content
    try:
        content = decrypt_content(
            paste["ciphertext"],
            paste["nonce"],
            paste["salt"],
            password,
        )
    except Exception as e:
        flash("Failed to decrypt. Wrong password?", "error")
        return redirect(url_for("index"))

    # Handle burn after reading
    will_burn = paste["burn_after_reading"]
    if will_burn:
        # Delete immediately after viewing
        del PASTES[paste_id]
        session.pop(f"paste_verified_{paste_id}", None)

    return render_template(
        "view.html", content=content, paste_id=paste_id, will_burn=will_burn
    )


@app.route("/verify/<paste_id>", methods=["POST"])
def verify(paste_id):
    password = request.form.get("password", "")
    paste = PASTES.get(paste_id)

    if not paste:
        abort(404)

    if paste["expires_at"] and datetime.now() > paste["expires_at"]:
        del PASTES[paste_id]
        flash("This paste has expired", "error")
        return redirect(url_for("index"))

    # Verify password by attempting decryption
    try:
        decrypt_content(paste["ciphertext"], paste["nonce"], paste["salt"], password)
        session[f"paste_verified_{paste_id}"] = password
        return redirect(url_for("view", paste_id=paste_id))
    except Exception:
        flash("Incorrect password", "error")
        return render_template("password_prompt.html", paste_id=paste_id, error=True)


@app.route("/raw/<paste_id>")
def raw(paste_id):
    """View paste as raw text (requires password if protected)."""
    paste = PASTES.get(paste_id)
    if not paste:
        abort(404)

    if paste["expires_at"] and datetime.now() > paste["expires_at"]:
        del PASTES[paste_id]
        abort(404)

    needs_password = paste["has_password"]
    password = get_verified_password(paste_id)

    if needs_password and not password:
        abort(403)

    try:
        content = decrypt_content(
            paste["ciphertext"], paste["nonce"], paste["salt"], password
        )
    except Exception:
        abort(500)

    if paste["burn_after_reading"]:
        del PASTES[paste_id]
        session.pop(f"paste_verified_{paste_id}", None)

    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Paste not found or has expired"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", message="Password required"), 403


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
