"""Analytics aggregation service."""

from datetime import datetime, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import Checkin, Habit


def get_analytics(habit_id, period="weekly", start_date=None, end_date=None):
    habit = Habit.query.get(habit_id)
    if not habit:
        return None

    now = datetime.utcnow()
    if not end_date:
        end_date = now.date()
    if not start_date:
        if period == "monthly":
            start_date = now.date() - timedelta(days=30)
        else:
            start_date = now.date() - timedelta(days=7)

    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace("Z", "")).date()
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace("Z", "")).date()

    checkins = Checkin.query.filter(
        Checkin.habit_id == habit_id,
        func.date(Checkin.completed_at) >= start_date,
        func.date(Checkin.completed_at) <= end_date,
    ).all()

    completed_dates = {c.completed_at.date() for c in checkins}

    delta = end_date - start_date
    num_days = delta.days + 1

    data = []
    total_completed = 0
    total_target = num_days * habit.target_count

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        completed = 1 if current_date in completed_dates else 0
        total_completed += completed
        data.append(
            {
                "date": current_date.isoformat(),
                "completed": completed,
                "target": habit.target_count,
            }
        )

    completion_rate = total_completed / total_target if total_target > 0 else 0.0

    return {
        "habit_id": habit_id,
        "period": period,
        "data": data,
        "summary": {
            "total_completed": total_completed,
            "total_target": total_target,
            "completion_rate": round(completion_rate, 2),
        },
    }


def get_summary(user_id):
    habits = Habit.query.filter_by(user_id=user_id, is_active=True).all()

    total_habits = len(habits)
    active_habits = total_habits
    now = datetime.utcnow().date()
    today_checkins = Checkin.query.filter(
        Checkin.user_id == user_id,
        func.date(Checkin.completed_at) == now,
    ).all()

    total_checkins = len(today_checkins)
    habits_due_today = active_habits

    overall_rate = total_checkins / habits_due_today if habits_due_today > 0 else 0.0

    best_streak = 0
    for habit in habits:
        from app.services.streak import calculate_streak

        streak = calculate_streak(habit.id)
        if streak["current_streak"] > best_streak:
            best_streak = streak["current_streak"]

    by_category = []
    for habit in habits:
        if habit.category:
            cat_name = habit.category.name
            existing = next((c for c in by_category if c["category"] == cat_name), None)
            if existing:
                existing["habits"] += 1
            else:
                by_category.append(
                    {
                        "category": cat_name,
                        "habits": 1,
                        "completion_rate": 0.0,
                    }
                )

    return {
        "total_habits": total_habits,
        "active_habits": active_habits,
        "overall_completion_rate": round(overall_rate, 2),
        "best_streak": best_streak,
        "total_checkins_today": total_checkins,
        "habits_due_today": habits_due_today,
        "by_category": by_category,
    }
