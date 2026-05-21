import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    custom_branding = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", backref="organization", lazy="dynamic")
    component_groups = db.relationship(
        "ComponentGroup", backref="organization", lazy="dynamic"
    )
    components = db.relationship("Component", backref="organization", lazy="dynamic")
    incidents = db.relationship("Incident", backref="organization", lazy="dynamic")
    settings = db.relationship("Settings", backref="organization", lazy="dynamic")

    def get_branding(self):
        if isinstance(self.custom_branding, str):
            return json.loads(self.custom_branding) if self.custom_branding else {}
        return self.custom_branding or {}

    def set_branding(self, data):
        self.custom_branding = json.dumps(data)

    def get_setting(self, key, default=None):
        setting = Settings.query.filter_by(organization_id=self.id, key=key).first()
        return setting.value if setting else default

    def set_setting(self, key, value):
        setting = Settings.query.filter_by(organization_id=self.id, key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(organization_id=self.id, key=key, value=value)
            db.session.add(setting)
        db.session.commit()

    def get_overall_status(self):
        if self.incidents.filter(Incident.status != "resolved").first():
            return "degraded"
        components = self.components.filter(Component.is_enabled == True).all()
        if not components:
            return "operational"
        for comp in components:
            latest = comp.latest_result()
            if latest and latest.status == "down":
                return "degraded"
        return "operational"

    def __repr__(self):
        return f"<Organization {self.slug}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="admin")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_owner(self):
        return self.role == "owner"

    def __repr__(self):
        return f"<User {self.email}>"


class ComponentGroup(db.Model):
    __tablename__ = "component_groups"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    components = db.relationship("Component", backref="group", lazy="dynamic")

    def get_status(self):
        for comp in self.components.filter(Component.is_enabled == True).all():
            latest = comp.latest_result()
            if latest and latest.status == "down":
                return "down"
            if latest and latest.status == "degraded":
                return "degraded"
        components = self.components.filter(Component.is_enabled == True).all()
        if not components:
            return "operational"
        return "operational"

    def get_uptime(self, days=30):
        components = self.components.filter(Component.is_enabled == True).all()
        if not components:
            return 100.0
        total_uptime = 0
        for comp in components:
            total_uptime += comp.get_uptime(days)
        return total_uptime / len(components) if components else 100.0

    def __repr__(self):
        return f"<ComponentGroup {self.name}>"


class Component(db.Model):
    __tablename__ = "components"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    group_id = db.Column(db.Integer, db.ForeignKey("component_groups.id"))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    check_type = db.Column(db.String(20), default="http")
    check_url = db.Column(db.String(500))
    check_method = db.Column(db.String(10), default="GET")
    check_timeout = db.Column(db.Integer, default=30)
    check_interval = db.Column(db.Integer, default=60)
    check_expected_status = db.Column(db.Integer, default=200)
    check_headers = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    check_results = db.relationship(
        "CheckResult",
        backref="component",
        lazy="dynamic",
        order_by="CheckResult.checked_at.desc()",
    )

    def latest_result(self):
        return self.check_results.first()

    def get_uptime(self, days=30):
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        results = self.check_results.filter(CheckResult.checked_at >= cutoff).all()
        if not results:
            return 100.0
        total = len(results)
        operational = sum(1 for r in results if r.status == "operational")
        return (operational / total) * 100

    def get_history(self, hours=24):
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.check_results.filter(CheckResult.checked_at >= cutoff)
            .order_by(CheckResult.checked_at.asc())
            .all()
        )

    def get_status(self):
        latest = self.latest_result()
        return latest.status if latest else "unknown"

    def __repr__(self):
        return f"<Component {self.name}>"


class CheckResult(db.Model):
    __tablename__ = "check_results"

    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("components.id"), nullable=False)
    status = db.Column(db.String(20))
    response_time_ms = db.Column(db.Integer)
    status_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CheckResult {self.component_id}: {self.status}>"


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default="minor")
    status = db.Column(db.String(20), default="investigating")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    timeline = db.relationship(
        "IncidentTimeline",
        backref="incident",
        lazy="dynamic",
        order_by="IncidentTimeline.created_at.desc()",
    )

    def is_resolved(self):
        return self.status == "resolved"

    def __repr__(self):
        return f"<Incident {self.id}: {self.title}>"


class IncidentTimeline(db.Model):
    __tablename__ = "incident_timeline"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False)
    status = db.Column(db.String(20))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IncidentTimeline {self.id}>"


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),
    )

    def __repr__(self):
        return f"<Settings {self.key}>"
