import os
import json
import uuid
import sqlite3
from flask import Flask, render_template, request, jsonify, g

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chartcraft.db')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

PORT = int(os.environ.get('PORT', 5000))


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db_once():
    with app.app_context():
        db = sqlite3.connect(app.config['DATABASE'])
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
        with open(schema_path, 'r') as f:
            db.executescript(f.read())
        db.close()


init_db_once()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gallery')
def gallery():
    return render_template('gallery.html')


def is_valid_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


@app.route('/chart/<chart_id>')
def view_chart(chart_id):
    if not is_valid_uuid(chart_id):
        return render_template('view.html', chart=None), 404
    db = get_db()
    chart = db.execute('SELECT * FROM charts WHERE id = ?', (chart_id,)).fetchone()
    if chart is None:
        return render_template('view.html', chart=None), 404
    return render_template('view.html', chart=dict(chart))


@app.route('/api/charts', methods=['POST'])
def save_chart():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400

        title = data.get('title', '').strip()
        raw_data = data.get('data', '')
        chart_config = data.get('config')
        thumbnail = data.get('thumbnail_base64', '')

        if not title:
            return jsonify({'error': 'Title is required'}), 400
        if not raw_data:
            return jsonify({'error': 'Data is required'}), 400
        if not chart_config:
            return jsonify({'error': 'Chart config is required'}), 400

        chart_id = str(uuid.uuid4())
        config_json = json.dumps(chart_config) if isinstance(chart_config, dict) else chart_config

        db = get_db()
        db.execute(
            'INSERT INTO charts (id, title, raw_data, chart_config, thumbnail) VALUES (?, ?, ?, ?, ?)',
            (chart_id, title, raw_data, config_json, thumbnail)
        )
        db.commit()

        return jsonify({
            'id': chart_id,
            'url': f'/chart/{chart_id}'
        }), 201

    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON in config'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/charts', methods=['GET'])
def list_charts():
    try:
        db = get_db()
        charts = db.execute(
            'SELECT id, title, thumbnail, created_at FROM charts ORDER BY created_at DESC'
        ).fetchall()
        return jsonify([dict(row) for row in charts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/charts/<chart_id>', methods=['DELETE'])
def delete_chart(chart_id):
    if not is_valid_uuid(chart_id):
        return jsonify({'error': 'Invalid chart ID'}), 400
    try:
        db = get_db()
        result = db.execute('DELETE FROM charts WHERE id = ?', (chart_id,))
        db.commit()
        if result.rowcount == 0:
            return jsonify({'error': 'Chart not found'}), 404
        return jsonify({'message': 'Chart deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=os.environ.get('FLASK_DEBUG', '0') == '1')
