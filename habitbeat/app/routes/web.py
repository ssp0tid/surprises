"""HTML routes."""

from flask import Blueprint, render_template, request

from app.api.auth import token_required

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    return render_template("index.html")


@web_bp.route("/habits")
def habits_page():
    return render_template("habits.html")


@web_bp.route("/habits/<int:habit_id>")
def habit_detail_page(habit_id):
    return render_template("habit_detail.html", habit_id=habit_id)


@web_bp.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@web_bp.route("/settings")
def settings_page():
    return render_template("settings.html")
