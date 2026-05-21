"""Reminder API endpoints."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.api.auth import token_required
from app.models import Habit, Reminder
from app.services.notifications import (
    cancel_reminders_for_habit,
    schedule_reminder as schedule,
)
from app.utils.errors import NotFoundError, ValidationError

reminders_bp = Blueprint("reminders", __name__)


@reminders_bp.route("", methods=["GET"])
@token_required
def list_reminders(current_user):
    status = request.args.get("status")
    query = Reminder.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)

    reminders = query.order_by(Reminder.scheduled_at).all()
    return jsonify(
        {
            "reminders": [r.to_dict() for r in reminders],
            "total": len(reminders),
        }
    ), 200


@reminders_bp.route("", methods=["POST"])
@token_required
def create_reminder(current_user):
    data = request.get_json() or {}
    habit_id = data.get("habit_id")
    scheduled_at = data.get("scheduled_at")
    external_url = data.get("external_url")

    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    if not scheduled_at:
        raise ValidationError(
            message="scheduled_at is required",
            details=[{"field": "scheduled_at", "message": "Required"}],
        )

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", ""))
    except ValueError:
        raise ValidationError(
            message="Invalid date format",
            details=[{"field": "scheduled_at", "message": "Use ISO format"}],
        )

    reminder = schedule(habit_id, current_user.id, scheduled_at, external_url)
    db.session.commit()

    return jsonify(
        {
            "id": reminder.id,
            "message": "Reminder scheduled successfully",
        }
    ), 201


@reminders_bp.route("/<int:reminder_id>", methods=["PUT"])
@token_required
def update_reminder(current_user, reminder_id):
    reminder = Reminder.query.get(reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise NotFoundError(message="Reminder not found")

    data = request.get_json() or {}
    if "scheduled_at" in data:
        try:
            reminder.scheduled_at = datetime.fromisoformat(
                data["scheduled_at"].replace("Z", "")
            )
        except ValueError:
            raise ValidationError(message="Invalid date format")
    if "external_url" in data:
        reminder.external_url = data["external_url"]
    if "status" in data:
        reminder.status = data["status"]

    db.session.commit()

    return jsonify(
        {
            "id": reminder.id,
            "message": "Reminder updated successfully",
        }
    ), 200


@reminders_bp.route("/<int:reminder_id>", methods=["DELETE"])
@token_required
def delete_reminder(current_user, reminder_id):
    reminder = Reminder.query.get(reminder_id)
    if not reminder or reminder.user_id != current_user.id:
        raise NotFoundError(message="Reminder not found")

    db.session.delete(reminder)
    db.session.commit()

    return jsonify({"message": "Reminder deleted successfully"}), 200
