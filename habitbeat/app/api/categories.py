"""Category endpoints."""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.api.auth import token_required
from app.models import Category, Habit
from app.utils.errors import DuplicateError, NotFoundError
from app.utils.validators import validate_category_name, validate_hex_color

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("", methods=["GET"])
@token_required
def list_categories(current_user):
    categories = (
        Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    )
    return jsonify(
        {
            "categories": [c.to_dict() for c in categories],
            "total": len(categories),
        }
    ), 200


@categories_bp.route("", methods=["POST"])
@token_required
def create_category(current_user):
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    color = data.get("color", "#6366f1")
    icon = data.get("icon", "star")

    validate_category_name(name)
    validate_hex_color(color)

    existing = Category.query.filter_by(user_id=current_user.id, name=name).first()
    if existing:
        raise DuplicateError(
            message="Category already exists",
            details=[{"field": "name", "message": "Category name already in use"}],
        )

    category = Category(
        user_id=current_user.id,
        name=name,
        color=color,
        icon=icon,
    )
    db.session.add(category)
    db.session.commit()

    return jsonify(
        {
            "id": category.id,
            "name": category.name,
            "message": "Category created successfully",
        }
    ), 201


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@token_required
def update_category(current_user, category_id):
    category = Category.query.get(category_id)
    if not category or category.user_id != current_user.id:
        raise NotFoundError(message="Category not found")

    data = request.get_json() or {}
    if "name" in data:
        validate_category_name(data["name"])
        existing = Category.query.filter(
            Category.user_id == current_user.id,
            Category.name == data["name"],
            Category.id != category_id,
        ).first()
        if existing:
            raise DuplicateError(message="Category name already in use")
        category.name = data["name"]
    if "color" in data:
        validate_hex_color(data["color"])
        category.color = data["color"]
    if "icon" in data:
        category.icon = data["icon"]

    db.session.commit()

    return jsonify(
        {
            "id": category.id,
            "name": category.name,
            "message": "Category updated successfully",
        }
    ), 200


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@token_required
def delete_category(current_user, category_id):
    category = Category.query.get(category_id)
    if not category or category.user_id != current_user.id:
        raise NotFoundError(message="Category not found")

    Habit.query.filter_by(category_id=category_id).update({"category_id": None})
    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category deleted successfully"}), 200
