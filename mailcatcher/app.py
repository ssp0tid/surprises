import os
import sqlite3
import json

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    abort,
)
from bleach import clean


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "mailcatcher.db")
EMAILS_DIR = os.path.join(DATA_DIR, "emails")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMAILS_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mailcatcher-dev-secret-key")

ALLOWED_TAGS = [
    "p",
    "br",
    "b",
    "i",
    "u",
    "em",
    "strong",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "table",
    "tr",
    "td",
    "th",
    "thead",
    "tbody",
]

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            subject TEXT,
            sender TEXT,
            recipients TEXT,
            date TIMESTAMP,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            text_body TEXT,
            html_body TEXT,
            headers TEXT,
            has_attachments INTEGER DEFAULT 0,
            eml_filename TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at DESC)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)")
    conn.commit()
    conn.close()


def sanitize_html(html_content):
    if not html_content:
        return ""
    return clean(html_content, tags=ALLOWED_TAGS, strip=True)


def validate_email_id(email_id):
    try:
        return int(email_id)
    except (ValueError, TypeError):
        return None


def validate_pagination_params(page, per_page):
    try:
        page = max(1, int(page)) if page else 1
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = (
            max(1, min(MAX_PER_PAGE, int(per_page))) if per_page else DEFAULT_PER_PAGE
        )
    except (ValueError, TypeError):
        per_page = DEFAULT_PER_PAGE

    return page, per_page


def get_email_by_id(email_id):
    conn = get_db_connection()
    email = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    conn.close()
    return email


def delete_email_from_db(email_id):
    email = get_email_by_id(email_id)
    if email and email["eml_filename"]:
        eml_path = os.path.join(EMAILS_DIR, email["eml_filename"])
        if os.path.exists(eml_path):
            os.remove(eml_path)

    conn = get_db_connection()
    conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()


init_db()


@app.errorhandler(404)
def not_found_error(error):
    return render_template("error.html", error_code=404, message="Email not found"), 404


@app.errorhandler(400)
def bad_request_error(error):
    return render_template("error.html", error_code=400, message="Bad request"), 400


@app.errorhandler(500)
def internal_error(error):
    return render_template(
        "error.html", error_code=500, message="Internal server error"
    ), 500


@app.route("/")
def index():
    page, per_page = validate_pagination_params(
        request.args.get("page"), request.args.get("per_page")
    )

    subject_filter = request.args.get("subject", "").strip()
    sender_filter = request.args.get("sender", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    conn = get_db_connection()
    query = "SELECT * FROM emails WHERE 1=1"
    params = []

    if subject_filter:
        query += " AND subject LIKE ?"
        params.append(f"%{subject_filter}%")

    if sender_filter:
        query += " AND sender LIKE ?"
        params.append(f"%{sender_filter}%")

    if date_from:
        query += " AND date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND date <= ?"
        params.append(date_to)

    count_query = query.replace("SELECT *", "SELECT COUNT(*) as count")
    total = conn.execute(count_query, params).fetchone()["count"]

    query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    emails = conn.execute(query, params).fetchall()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        "index.html",
        emails=emails,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        filters={
            "subject": subject_filter,
            "sender": sender_filter,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


@app.route("/email/<email_id>")
def email_detail(email_id):
    email_id = validate_email_id(email_id)
    if not email_id:
        abort(400)

    email = get_email_by_id(email_id)
    if not email:
        abort(404)

    sanitized_html = sanitize_html(email["html_body"]) if email["html_body"] else ""

    headers = {}
    if email["headers"]:
        try:
            headers = json.loads(email["headers"])
        except (json.JSONDecodeError, TypeError):
            pass

    return render_template(
        "detail.html", email=email, sanitized_html=sanitized_html, headers=headers
    )


@app.route("/email/<email_id>/delete", methods=["POST"])
def delete_email(email_id):
    email_id = validate_email_id(email_id)
    if not email_id:
        flash("Invalid email ID", "error")
        return redirect(url_for("index"))

    email = get_email_by_id(email_id)
    if not email:
        flash("Email not found", "error")
        return redirect(url_for("index"))

    delete_email_from_db(email_id)
    flash("Email deleted successfully", "success")
    return redirect(url_for("index"))


@app.route("/emails/delete", methods=["POST"])
def bulk_delete():
    email_ids = request.form.getlist("email_ids")

    if not email_ids:
        flash("No emails selected", "error")
        return redirect(url_for("index"))

    deleted_count = 0
    for email_id in email_ids:
        valid_id = validate_email_id(email_id)
        if valid_id:
            delete_email_from_db(valid_id)
            deleted_count += 1

    flash(f"Deleted {deleted_count} email(s)", "success")
    return redirect(url_for("index"))


@app.route("/email/<email_id>/download")
def download_email(email_id):
    email_id = validate_email_id(email_id)
    if not email_id:
        abort(400)

    email = get_email_by_id(email_id)
    if not email:
        abort(404)

    if not email["eml_filename"]:
        abort(404)

    eml_path = os.path.join(EMAILS_DIR, email["eml_filename"])
    if not os.path.exists(eml_path):
        abort(404)

    return send_file(
        eml_path,
        mimetype="message/rfc822",
        as_attachment=True,
        download_name=f"email_{email_id}.eml",
    )


@app.route("/emails/clear", methods=["POST"])
def clear_all_emails():
    conn = get_db_connection()
    emails = conn.execute("SELECT eml_filename FROM emails").fetchall()

    for email in emails:
        if email["eml_filename"]:
            eml_path = os.path.join(EMAILS_DIR, email["eml_filename"])
            if os.path.exists(eml_path):
                os.remove(eml_path)

    conn.execute("DELETE FROM emails")
    conn.commit()
    conn.close()

    flash("All emails cleared", "success")
    return redirect(url_for("index"))


@app.route("/api/emails")
def api_emails_list():
    page, per_page = validate_pagination_params(
        request.args.get("page"), request.args.get("per_page")
    )

    conn = get_db_connection()
    query = "SELECT id, subject, sender, date, received_at, has_attachments FROM emails ORDER BY received_at DESC LIMIT ? OFFSET ?"
    emails = conn.execute(query, (per_page, (page - 1) * per_page)).fetchall()
    conn.close()

    return jsonify(
        {"emails": [dict(row) for row in emails], "page": page, "per_page": per_page}
    )


@app.route("/api/emails/<email_id>")
def api_email_detail(email_id):
    email_id = validate_email_id(email_id)
    if not email_id:
        return jsonify({"error": "Invalid email ID"}), 400

    email = get_email_by_id(email_id)
    if not email:
        return jsonify({"error": "Email not found"}), 404

    return jsonify(dict(email))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
