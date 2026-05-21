"""Authentication API endpoints."""

import os
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
import jwt
from flask import Blueprint, Flask, current_app, jsonify, request

from app.extensions import db
from app.models import User
from app.utils.errors import AuthenticationError, DuplicateError, ValidationError
from app.utils.validators import validate_email, validate_password

auth_bp = Blueprint("auth", __name__)


def generate_token(user_id, email):
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow()
        + timedelta(seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 86400))),
    }
    return jwt.encode(
        payload, os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"), algorithm="HS256"
    )


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError(message="Authentication required")

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            raise AuthenticationError(message="Invalid token format")

        try:
            payload = jwt.decode(
                token,
                os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"),
                algorithms=["HS256"],
            )
            user = User.query.get(payload["sub"])
            if not user:
                raise AuthenticationError(message="User not found")
        except jwt.ExpiredSignatureError:
            raise AuthenticationError(message="Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError(message="Invalid token")

        return f(user, *args, **kwargs)

    return decorated


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    validate_email(email)
    validate_password(password)

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise DuplicateError(
            message="User already exists",
            details=[{"field": "email", "message": "Email already registered"}],
        )

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user = User(email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id, user.email)

    return jsonify(
        {
            "message": "Registration successful",
            "user": user.to_dict(),
            "access_token": token,
        }
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    validate_email(email)
    validate_password(password, min_length=1)

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(
        password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        raise AuthenticationError(message="Invalid credentials")

    token = generate_token(user.id, user.email)

    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 86400)),
        }
    ), 200


@auth_bp.route("/refresh", methods=["POST"])
@token_required
def refresh_token(current_user):
    token = generate_token(current_user.id, current_user.email)
    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 86400)),
        }
    ), 200


@auth_bp.route("/logout", methods=["DELETE"])
@token_required
def logout(current_user):
    return jsonify({"message": "Logout successful"}), 200
