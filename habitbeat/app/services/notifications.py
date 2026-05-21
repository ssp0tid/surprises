"""Reminder scheduling service."""

import os
from datetime import datetime

import requests

from app.extensions import db
from app.models import Reminder


def schedule_reminder(habit_id, user_id, scheduled_at, external_url=None):
    reminder = Reminder(
        habit_id=habit_id,
        user_id=user_id,
        scheduled_at=scheduled_at,
        external_url=external_url or os.environ.get("DEFAULT_WEBHOOK_URL", ""),
        status="pending",
    )
    db.session.add(reminder)
    db.session.commit()
    return reminder


def process_pending_reminders():
    now = datetime.utcnow()
    pending = Reminder.query.filter(
        Reminder.status == "pending",
        Reminder.scheduled_at <= now,
    ).all()

    for reminder in pending:
        send_reminder(reminder)


def send_reminder(reminder):
    if not reminder.external_url:
        reminder.status = "failed"
        db.session.commit()
        return False

    try:
        response = requests.post(
            reminder.external_url,
            json={
                "habit_id": reminder.habit_id,
                "scheduled_at": reminder.scheduled_at.isoformat(),
            },
            timeout=10,
        )
        if response.status_code in [200, 201, 202]:
            reminder.status = "sent"
            reminder.sent_at = datetime.utcnow()
            db.session.commit()
            return True
    except Exception:
        pass

    if reminder.status == "pending":
        reminder.status = "failed"
        db.session.commit()
    return False


def cancel_reminders_for_habit(habit_id):
    Reminder.query.filter_by(habit_id=habit_id, status="pending").delete()
    db.session.commit()
