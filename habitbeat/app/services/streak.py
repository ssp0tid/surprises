"""Streak calculation service."""

from datetime import datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import Checkin, Habit


def calculate_streak(habit_id):
    habit = Habit.query.get(habit_id)
    if not habit:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "streak_start_date": None,
            "streak_end_date": None,
            "last_completed_date": None,
            "completion_rate_30d": 0.0,
            "completion_rate_90d": 0.0,
            "total_completions": 0,
        }

    checkins = (
        Checkin.query.filter_by(habit_id=habit_id)
        .order_by(Checkin.completed_at.desc())
        .all()
    )

    if not checkins:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "streak_start_date": None,
            "streak_end_date": None,
            "last_completed_date": None,
            "completion_rate_30d": 0.0,
            "completion_rate_90d": 0.0,
            "total_completions": 0,
        }

    completed_dates = {c.completed_at.date() for c in checkins}
    total_completions = len(completed_dates)

    now = datetime.utcnow().date()
    days_30 = (now - timedelta(days=30)).date()
    days_90 = (now - timedelta(days=90)).date()

    completions_30d = len([d for d in completed_dates if d >= days_30])
    completions_90d = len([d for d in completed_dates if d >= days_90])

    completion_rate_30d = completions_30d / 30 if 30 > 0 else 0.0
    completion_rate_90d = completions_90d / 90 if 90 > 0 else 0.0

    current_streak = 0
    current_date = now
    while current_date in completed_dates or (
        current_date == now and current_date not in completed_dates
    ):
        if current_date in completed_dates:
            current_streak += 1
            current_date -= timedelta(days=1)
        else:
            if current_date != now:
                break
            current_date -= timedelta(days=1)
        if current_streak > 365:
            break

    longest_streak = 0
    temp_streak = 0
    sorted_dates = sorted(completed_dates)
    for i, date in enumerate(sorted_dates):
        if i == 0:
            temp_streak = 1
        else:
            if (date - sorted_dates[i - 1]).days == 1:
                temp_streak += 1
            else:
                temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)

    last_completed = max(completed_dates) if completed_dates else None

    return {
        "current_streak": current_streak,
        "longest_streak": max(longest_streak, current_streak),
        "streak_start_date": (now - timedelta(days=current_streak - 1)).isoformat()
        if current_streak > 0
        else None,
        "streak_end_date": now.isoformat() if current_streak > 0 else None,
        "last_completed_date": last_completed.isoformat() if last_completed else None,
        "completion_rate_30d": round(completion_rate_30d, 2),
        "completion_rate_90d": round(completion_rate_90d, 2),
        "total_completions": total_completions,
    }


def get_streak_for_habit(habit_id):
    return calculate_streak(habit_id)
