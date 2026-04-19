"""
ClipStash - Flask Clipboard History Manager
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(basedir, 'clipstash.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Database Models
class ClipboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, default=False)
    tags = db.relationship(
        "Tag", backref="entry", lazy=True, cascade="all, delete-orphan"
    )


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    entry_id = db.Column(
        db.Integer, db.ForeignKey("clipboard_entry.id"), nullable=False
    )


# Routes
@app.route("/")
def index():
    search_query = request.args.get("q", "")
    filter_favorites = request.args.get("favorites") == "on"
    filter_tag = request.args.get("tag", "")

    query = ClipboardEntry.query

    if search_query:
        query = query.filter(ClipboardEntry.content.contains(search_query))

    if filter_favorites:
        query = query.filter(ClipboardEntry.is_favorite == True)

    if filter_tag:
        query = query.join(Tag).filter(Tag.name == filter_tag)

    entries = query.order_by(ClipboardEntry.timestamp.desc()).all()
    all_tags = db.session.query(Tag.name).distinct().all()
    all_tags = [t[0] for t in all_tags]

    return render_template(
        "index.html",
        entries=entries,
        all_tags=all_tags,
        search_query=search_query,
        filter_favorites=filter_favorites,
        filter_tag=filter_tag,
    )


@app.route("/add", methods=["POST"])
def add_entry():
    content = request.form.get("content", "").strip()
    tags_raw = request.form.get("tags", "").strip()

    if not content:
        return jsonify({"error": "Content is required"}), 400

    entry = ClipboardEntry(content=content)
    db.session.add(entry)
    db.session.flush()  # Get the entry ID

    # Process tags
    if tags_raw:
        tag_names = [t.strip() for t in tags_raw.split(",") if t.strip()]
        for tag_name in tag_names:
            tag = Tag(name=tag_name, entry=entry)
            db.session.add(tag)

    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:entry_id>")
def delete_entry(entry_id):
    entry = ClipboardEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/favorite/<int:entry_id>")
def toggle_favorite(entry_id):
    entry = ClipboardEntry.query.get_or_404(entry_id)
    entry.is_favorite = not entry.is_favorite
    db.session.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/add_tags/<int:entry_id>", methods=["POST"])
def add_tags(entry_id):
    entry = ClipboardEntry.query.get_or_404(entry_id)
    tags_raw = request.form.get("tags", "").strip()

    if tags_raw:
        tag_names = [t.strip() for t in tags_raw.split(",") if t.strip()]
        existing_tags = {tag.name for tag in entry.tags}

        for tag_name in tag_names:
            if tag_name not in existing_tags:
                tag = Tag(name=tag_name, entry=entry)
                db.session.add(tag)

        db.session.commit()

    return redirect(url_for("index"))


@app.route("/remove_tag/<int:entry_id>/<tag_name>")
def remove_tag(entry_id, tag_name):
    entry = ClipboardEntry.query.get_or_404(entry_id)
    tag = Tag.query.filter_by(entry_id=entry_id, name=tag_name).first()
    if tag:
        db.session.delete(tag)
        db.session.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/api/entries")
def api_entries():
    """API endpoint for JSON-based access"""
    search_query = request.args.get("q", "")
    favorites_only = request.args.get("favorites") == "true"

    query = ClipboardEntry.query

    if search_query:
        query = query.filter(ClipboardEntry.content.contains(search_query))

    if favorites_only:
        query = query.filter(ClipboardEntry.is_favorite == True)

    entries = query.order_by(ClipboardEntry.timestamp.desc()).all()

    return jsonify(
        [
            {
                "id": e.id,
                "content": e.content,
                "timestamp": e.timestamp.isoformat(),
                "is_favorite": e.is_favorite,
                "tags": [t.name for t in e.tags],
            }
            for e in entries
        ]
    )


# Initialize database
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
