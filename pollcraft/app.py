import json
import queue
import threading
from flask import Flask, request, jsonify, render_template, Response, abort

from database import init_db, create_poll, get_poll, get_options, cast_vote, close_poll, delete_poll, add_comment, get_comments

app = Flask(__name__)

# SSE subscribers: {slug: [queue, ...]}
subscribers = {}
subscribers_lock = threading.Lock()


def notify_subscribers(slug):
    poll = get_poll(slug)
    if poll is None:
        return
    options = get_options(poll['id'])
    total_votes = sum(o['votes'] for o in options)
    data = json.dumps({
        'options': options,
        'total_votes': total_votes,
        'poll_type': poll['poll_type']
    })
    with subscribers_lock:
        queues = subscribers.get(slug, [])
        for q in queues:
            q.put(data)


def get_voter_ip():
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr


# --- Page Routes ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create')
def create_page():
    return render_template('create.html')


@app.route('/p/<slug>')
def vote_page(slug):
    poll = get_poll(slug)
    if poll is None:
        abort(404)
    options = get_options(poll['id'])
    return render_template('vote.html', poll=poll, options=options)


@app.route('/r/<slug>')
def results_page(slug):
    poll = get_poll(slug)
    if poll is None:
        abort(404)
    options = get_options(poll['id'])
    return render_template('results.html', poll=poll, options=options)


@app.route('/manage/<slug>')
def manage_page(slug):
    token = request.args.get('token', '')
    poll = get_poll(slug)
    if poll is None:
        abort(404)
    if poll['admin_token'] != token:
        abort(403)
    options = get_options(poll['id'])
    return render_template('manage.html', poll=poll, options=options, token=token)


# --- API Routes ---

@app.route('/api/polls', methods=['POST'])
def api_create_poll():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    if len(title) > 200:
        return jsonify({'error': 'Title must be 200 characters or less'}), 400

    description = (data.get('description') or '').strip()
    if len(description) > 1000:
        return jsonify({'error': 'Description must be 1000 characters or less'}), 400

    options = data.get('options', [])
    if not isinstance(options, list):
        return jsonify({'error': 'Options must be a list'}), 400

    options = [o.strip() for o in options if isinstance(o, str) and o.strip()]
    if len(options) < 2:
        return jsonify({'error': 'At least 2 options are required'}), 400
    if len(options) > 20:
        return jsonify({'error': 'Maximum 20 options allowed'}), 400
    for o in options:
        if len(o) > 200:
            return jsonify({'error': 'Each option must be 200 characters or less'}), 400

    poll_type = data.get('poll_type', 'single')
    if poll_type not in ('single', 'multiple'):
        return jsonify({'error': 'poll_type must be "single" or "multiple"'}), 400

    allow_comments = bool(data.get('allow_comments', False))

    try:
        slug, admin_token = create_poll(title, description, options, poll_type, allow_comments)
    except RuntimeError:
        return jsonify({'error': 'Failed to create poll. Please try again.'}), 503

    return jsonify({
        'slug': slug,
        'admin_token': admin_token,
        'vote_url': f'/p/{slug}',
        'results_url': f'/r/{slug}',
        'manage_url': f'/manage/{slug}?token={admin_token}'
    }), 201


@app.route('/api/polls/<slug>/vote', methods=['POST'])
def api_vote(slug):
    poll = get_poll(slug)
    if poll is None:
        return jsonify({'error': 'Poll not found'}), 404
    if poll['closed_at'] is not None:
        return jsonify({'error': 'Poll is closed'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    option_ids = data.get('option_ids', [])
    if not isinstance(option_ids, list) or len(option_ids) == 0:
        return jsonify({'error': 'At least one option must be selected'}), 400

    if poll['poll_type'] == 'single' and len(option_ids) > 1:
        return jsonify({'error': 'Only one option allowed for single-choice polls'}), 400

    try:
        option_ids = [int(oid) for oid in option_ids]
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid option IDs'}), 400

    voter_ip = get_voter_ip()
    success = cast_vote(poll['id'], option_ids, voter_ip)

    if not success:
        return jsonify({'error': 'You have already voted on this poll'}), 409

    notify_subscribers(slug)
    return jsonify({'message': 'Vote recorded'}), 200


@app.route('/api/polls/<slug>/results', methods=['GET'])
def api_results(slug):
    poll = get_poll(slug)
    if poll is None:
        return jsonify({'error': 'Poll not found'}), 404
    options = get_options(poll['id'])
    total_votes = sum(o['votes'] for o in options)
    return jsonify({
        'poll': {
            'title': poll['title'],
            'description': poll['description'],
            'poll_type': poll['poll_type'],
            'closed_at': poll['closed_at']
        },
        'options': options,
        'total_votes': total_votes
    })


@app.route('/api/polls/<slug>/stream')
def api_stream(slug):
    poll = get_poll(slug)
    if poll is None:
        abort(404)

    q = queue.Queue()
    with subscribers_lock:
        if slug not in subscribers:
            subscribers[slug] = []
        subscribers[slug].append(q)

    def event_stream():
        try:
            options = get_options(poll['id'])
            total_votes = sum(o['votes'] for o in options)
            initial = json.dumps({
                'options': options,
                'total_votes': total_votes,
                'poll_type': poll['poll_type']
            })
            yield f"data: {initial}\n\n"

            while True:
                try:
                    data = q.get(timeout=30)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with subscribers_lock:
                if slug in subscribers:
                    try:
                        subscribers[slug].remove(q)
                    except ValueError:
                        pass
                    if not subscribers[slug]:
                        del subscribers[slug]

    return Response(event_stream(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/polls/<slug>/close', methods=['POST'])
def api_close_poll(slug):
    admin_token = request.headers.get('X-Admin-Token', '')
    if not admin_token:
        return jsonify({'error': 'Admin token required'}), 401

    success = close_poll(slug, admin_token)
    if not success:
        return jsonify({'error': 'Invalid slug or admin token'}), 403

    return jsonify({'message': 'Poll closed'}), 200


@app.route('/api/polls/<slug>', methods=['DELETE'])
def api_delete_poll(slug):
    admin_token = request.headers.get('X-Admin-Token', '')
    if not admin_token:
        return jsonify({'error': 'Admin token required'}), 401

    success = delete_poll(slug, admin_token)
    if not success:
        return jsonify({'error': 'Invalid slug or admin token'}), 403

    return jsonify({'message': 'Poll deleted'}), 200


@app.route('/api/polls/<slug>/comments', methods=['GET'])
def api_get_comments(slug):
    poll = get_poll(slug)
    if poll is None:
        return jsonify({'error': 'Poll not found'}), 404
    comments = get_comments(poll['id'])
    return jsonify({'comments': comments})


@app.route('/api/polls/<slug>/comments', methods=['POST'])
def api_add_comment(slug):
    poll = get_poll(slug)
    if poll is None:
        return jsonify({'error': 'Poll not found'}), 404
    if not poll['allow_comments']:
        return jsonify({'error': 'Comments are not enabled for this poll'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Comment text is required'}), 400
    if len(text) > 1000:
        return jsonify({'error': 'Comment must be 1000 characters or less'}), 400

    author = (data.get('author') or '').strip() or 'Anonymous'
    if len(author) > 100:
        return jsonify({'error': 'Author name must be 100 characters or less'}), 400

    comment = add_comment(poll['id'], text, author)
    return jsonify(comment), 201


# --- Error Handlers ---

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('base.html', error='Page not found'), 404


@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('base.html', error='Access denied'), 403


@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000, threaded=True)
