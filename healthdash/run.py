#!/usr/bin/env python3
"""Development entry point for HealthDash."""

import os
from dotenv import load_dotenv

load_dotenv()

from healthdash import create_app
from healthdash.models import db

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
