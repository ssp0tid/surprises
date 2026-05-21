"""Analytics endpoints."""

from flask import Blueprint, jsonify, request

from app.api.auth import token_required
from app.models import Habit
from app.services.analytics import get_analytics, get_summary
from app.services.streak import get_streak_for_habit
from app.utils.errors import NotFoundError

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/habits/<int:habit_id>/streak", methods=["GET"])
@token_required
def get_streak(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    streak = get_streak_for_habit(habit_id)
    return jsonify(streak), 200


@analytics_bp.route("/habits/<int:habit_id>/analytics", methods=["GET"])
@token_required
def get_habit_analytics(current_user, habit_id):
    habit = Habit.query.get(habit_id)
    if not habit or habit.user_id != current_user.id:
        raise NotFoundError(message="Habit not found")

    period = request.args.get("period", "weekly")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    analytics = get_analytics(habit_id, period, start_date, end_date)
    return jsonify(analytics), 200


@analytics_bp.route("/summary", methods=["GET"])
@token_required
def get_dashboard_summary(current_user):
    summary = get_summary(current_user.id)
    return jsonify(summary), 200
