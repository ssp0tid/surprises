"""Check-in endpoints."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.api.auth import token_required
from app.models import Checkin, Habit
from app.utils.errors import NotFoundError, ValidationError

checkins_bp = Blueprint("checkins", __name__)


@checkins_bp.route("/habits/<int:habit_id>/checkins", methods=["GET"])
@token_required
def list_checkins(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    limit = request.args.get("limit", 30, type=int)
    checkins = (
        Checkin.query.filter_by(habit_id=habit_id)
        .order_by(Checkin.completed_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "checkins": [c.to_dict() for c in checkins],
            "total": len(checkins),
        }
    ), 200


@checkins_bp.route("/habits/<int:habit_id>/checkins", methods=["POST"])
@token_required
def create_checkin(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    data = request.get_json() or {}
    completed_at = data.get("completed_at")
    note = data.get("note", "")

    if completed_at:
        try:
            completed_at = datetime.fromisoformat(completed_at.replace("Z", ""))
        except ValueError:
            raise ValidationError(
                message="Invalid date format",
                details=[{"field": "completed_at", "message": "Use ISO format"}],
            )
    else:
        completed_at = datetime.utcnow()

    existing = Checkin.query.filter(
        Checkin.habit_id == habit_id,
        Checkin.completed_at >= completed_at.replace(hour=0, minute=0, second=0),
        Checkin.completed_at < completed_at.replace(hour=23, minute=59, second=59),
    ).first()

    if existing:
        if note:
            existing.note = note
            db.session.commit()
        return jsonify(
            {
                "id": existing.id,
                "habit_id": habit_id,
                "completed_at": existing.completed_at.isoformat() + "Z",
                "message": "Check-in already exists, updated note",
            }
        ), 200

    checkin = Checkin(
        habit_id=habit_id,
        user_id=current_user.id,
        completed_at=completed_at,
        note=note,
    )
    db.session.add(checkin)
    db.session.commit()

    return jsonify(
        {
            "id": checkin.id,
            "habit_id": habit_id,
            "completed_at": checkin.completed_at.isoformat() + "Z",
            "message": "Check-in recorded",
        }
    ), 201


@checkins_bp.route("/checkins/<int:checkin_id>", methods=["DELETE"])
@token_required
def delete_checkin(current_user, checkin_id):
    checkin = Checkin.query.get(checkin_id)
    if not checkin or checkin.user_id != current_user.id:
        raise NotFoundError(message="Check-in not found")

    db.session.delete(checkin)
    db.session.commit()

    return jsonify({"message": "Check-in deleted successfully"}), 200
