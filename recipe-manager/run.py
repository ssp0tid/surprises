#!/usr/bin/env python3
"""Run the Recipe Manager Flask application."""

import os
from app import app, db

if __name__ == '__main__':
    # Create database if not exists
    with app.app_context():
        db.create_all()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)