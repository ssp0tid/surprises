"""SQLAlchemy database models."""

from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    habits = db.relationship("Habit", backref="user", lazy="dynamic")
    categories = db.relationship("Category", backref="user", lazy="dynamic")
    checkins = db.relationship("Checkin", backref="user", lazy="dynamic")
    reminders = db.relationship("Reminder", backref="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat() + "Z",
        }


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default="#6366f1")
    icon = db.Column(db.String(50), default="star")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    habits = db.relationship("Habit", backref="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "created_at": self.created_at.isoformat() + "Z",
        }


class Habit(db.Model):
    __tablename__ = "habits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    frequency = db.Column(db.String(20), nullable=False, default="daily")
    target_count = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.Time, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    checkins = db.relationship("Checkin", backref="habit", lazy="dynamic")
    reminders = db.relationship("Reminder", backref="habit", lazy="dynamic")

    def to_dict(self, include_streak=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "frequency": self.frequency,
            "target_count": self.target_count,
            "is_active": self.is_active,
            "reminder_time": self.reminder_time.isoformat()
            if self.reminder_time
            else None,
            "created_at": self.created_at.isoformat() + "Z",
        }
        if self.category:
            data["category"] = self.category.to_dict()
        if include_streak:
            from app.services.streak import calculate_streak

            streak = calculate_streak(self.id)
            data["current_streak"] = streak["current_streak"]
            data["longest_streak"] = streak["longest_streak"]
            data["completion_rate"] = streak["completion_rate_30d"]
        return data


class Checkin(db.Model):
    __tablename__ = "checkins"

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "habit_id", "completed_at", name="unique_habit_checkin_per_day"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "habit_id": self.habit_id,
            "completed_at": self.completed_at.isoformat() + "Z",
            "note": self.note,
            "created_at": self.created_at.isoformat() + "Z",
        }


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="pending")
    external_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "habit": {"id": self.habit.id, "name": self.habit.name}
            if self.habit
            else None,
            "scheduled_at": self.scheduled_at.isoformat() + "Z",
            "sent_at": self.sent_at.isoformat() + "Z" if self.sent_at else None,
            "status": self.status,
            "external_url": self.external_url,
            "created_at": self.created_at.isoformat() + "Z",
        }
