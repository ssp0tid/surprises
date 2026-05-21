import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SelectField,
    IntegerField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Optional,
    NumberRange,
    ValidationError,
)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    organization_name = StringField(
        "Organization Name", validators=[DataRequired(), Length(min=2, max=200)]
    )
    organization_slug = StringField(
        "Organization Slug", validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )

    def validate_organization_slug(self, field):
        pattern = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
        if not re.match(pattern, field.data):
            raise ValidationError(
                "Slug must be lowercase alphanumeric with hyphens, "
                "starting and ending with alphanumeric"
            )
        from app.models import Organization

        if Organization.query.filter_by(slug=field.data).first():
            raise ValidationError("This slug is already taken")
        from app.models import User

        if User.query.filter_by(email=self.email.data).first():
            raise ValidationError("This email is already registered")


class UserRegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )


class ComponentForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    group_id = SelectField("Group", coerce=int, validators=[Optional()])
    check_type = SelectField(
        "Check Type",
        choices=[("http", "HTTP"), ("tcp", "TCP"), ("ping", "Ping")],
        validators=[DataRequired()],
    )
    check_url = StringField("Check URL", validators=[Optional()])
    check_method = SelectField(
        "Method",
        choices=[("GET", "GET"), ("POST", "POST"), ("HEAD", "HEAD")],
        validators=[DataRequired()],
    )
    check_timeout = IntegerField(
        "Timeout (seconds)", validators=[DataRequired(), NumberRange(min=1, max=60)]
    )
    check_interval = IntegerField(
        "Check Interval (seconds)",
        validators=[DataRequired(), NumberRange(min=10, max=3600)],
    )
    check_expected_status = IntegerField(
        "Expected Status", validators=[DataRequired(), NumberRange(min=100, max=599)]
    )
    check_headers = TextAreaField("Headers (JSON)", validators=[Optional()])
    is_enabled = BooleanField("Enabled")
    display_order = IntegerField("Display Order", validators=[Optional()])

    def validate_check_url(self, field):
        if self.check_type.data == "http" and not field.data:
            raise ValidationError("URL is required for HTTP checks")


class ComponentGroupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    display_order = IntegerField("Display Order", validators=[Optional()])


class IncidentForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=500)])
    description = TextAreaField("Description", validators=[Optional()])
    severity = SelectField(
        "Severity",
        choices=[("critical", "Critical"), ("major", "Major"), ("minor", "Minor")],
        validators=[DataRequired()],
    )


class IncidentUpdateForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("investigating", "Investigating"),
            ("identified", "Identified"),
            ("monitoring", "Monitoring"),
            ("resolved", "Resolved"),
        ],
        validators=[DataRequired()],
    )
    message = TextAreaField("Message", validators=[DataRequired()])


class SettingsForm(FlaskForm):
    organization_name = StringField(
        "Organization Name", validators=[DataRequired(), Length(max=200)]
    )
    primary_color = StringField("Primary Color", validators=[Optional()])
    custom_css = TextAreaField("Custom CSS", validators=[Optional()])
