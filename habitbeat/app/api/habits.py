"""Habit CRUD endpoints."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.api.auth import token_required
from app.models import Habit
from app.utils.errors import NotFoundError, PermissionError
from app.utils.validators import validate_frequency, validate_habit_name

habits_bp = Blueprint("habits", __name__)


@habits_bp.route("", methods=["GET"])
@token_required
def list_habits(current_user):
    active_only = request.args.get("active", "true").lower() == "true"
    query = Habit.query.filter_by(user_id=current_user.id)
    if active_only:
        query = query.filter_by(is_active=True)

    habits = query.order_by(Habit.created_at.desc()).all()
    return jsonify(
        {
            "habits": [h.to_dict(include_streak=True) for h in habits],
            "total": len(habits),
            "active": sum(1 for h in habits if h.is_active),
        }
    ), 200


@habits_bp.route("", methods=["POST"])
@token_required
def create_habit(current_user):
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    description = data.get("description", "")
    category_id = data.get("category_id")
    frequency = data.get("frequency", "daily")
    target_count = data.get("target_count", 1)
    reminder_time = data.get("reminder_time")

    validate_habit_name(name)
    validate_frequency(frequency)

    habit = Habit(
        user_id=current_user.id,
        name=name,
        description=description,
        category_id=category_id,
        frequency=frequency,
        target_count=target_count,
        reminder_time=datetime.strptime(reminder_time, "%H:%M:%S").time()
        if reminder_time
        else None,
    )
    db.session.add(habit)
    db.session.commit()

    return jsonify(
        {
            "id": habit.id,
            "name": habit.name,
            "message": "Habit created successfully",
        }
    ), 201


@habits_bp.route("/<int:habit_id>", methods=["GET"])
@token_required
def get_habit(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    return jsonify(habit.to_dict(include_streak=True)), 200


@habits_bp.route("/<int:habit_id>", methods=["PUT"])
@token_required
def update_habit(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    data = request.get_json() or {}
    if "name" in data:
        validate_habit_name(data["name"])
        habit.name = data["name"]
    if "description" in data:
        habit.description = data["description"]
    if "category_id" in data:
        habit.category_id = data["category_id"]
    if "frequency" in data:
        validate_frequency(data["frequency"])
        habit.frequency = data["frequency"]
    if "target_count" in data:
        habit.target_count = data["target_count"]
    if "is_active" in data:
        habit.is_active = data["is_active"]
    if "reminder_time" in data:
        habit.reminder_time = (
            datetime.strptime(data["reminder_time"], "%H:%M:%S").time()
            if data["reminder_time"]
            else None
        )

    habit.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(
        {
            "id": habit.id,
            "name": habit.name,
            "message": "Habit updated successfully",
        }
    ), 200


@habits_bp.route("/<int:habit_id>", methods=["DELETE"])
@token_required
def delete_habit(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    habit.is_active = False
    db.session.commit()

    return jsonify({"message": "Habit deleted successfully"}), 200
