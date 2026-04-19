from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Service(db.Model):
    """Service endpoint to monitor"""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    method = db.Column(db.String(10), default="GET")  # GET, POST, HEAD
    expected_status = db.Column(db.Integer, default=200)
    check_interval = db.Column(db.Integer, default=60)  # seconds
    timeout = db.Column(db.Integer, default=10)  # seconds
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    checks = db.relationship(
        "HealthCheck",
        backref="service",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="HealthCheck.timestamp.desc()",
    )

    def __repr__(self):
        return f"<Service {self.name}>"

    @property
    def uptime_percentage(self):
        """Calculate uptime percentage from last 100 checks"""
        recent_checks = self.checks.limit(100).all()
        if not recent_checks:
            return None
        successful = sum(1 for c in recent_checks if c.is_up)
        return round((successful / len(recent_checks)) * 100, 2)

    @property
    def avg_response_time(self):
        """Average response time from last 100 checks (ms)"""
        recent_checks = self.checks.limit(100).all()
        times = [c.response_time for c in recent_checks if c.response_time is not None]
        return round(sum(times) / len(times), 2) if times else None


class HealthCheck(db.Model):
    """Individual health check result"""

    __tablename__ = "health_checks"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_up = db.Column(db.Boolean, nullable=False)
    response_time = db.Column(db.Float, nullable=True)  # milliseconds
    status_code = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<HealthCheck {self.service_id} {self.timestamp}>"
