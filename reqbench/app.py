import json
import time

import requests as http_requests
from flask import Flask, request, jsonify, render_template

import database

app = Flask(__name__)

REQUEST_TIMEOUT = 30


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/send', methods=['POST'])
def send_request():
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({'error': 'URL is required'}), 400

    method = data.get('method', 'GET').upper()
    url = data.get('url', '')
    headers = {}
    body = data.get('body', '')
    body_type = data.get('body_type', 'json')
    params = {}

    data['method'] = method
    data['url'] = url

    for h in data.get('headers', []):
        key = h.get('key', '').strip()
        value = h.get('value', '')
        if key:
            headers[key] = value

    for p in data.get('params', []):
        key = p.get('key', '').strip()
        value = p.get('value', '')
        if key:
            params[key] = value

    request_kwargs = {
        'method': method,
        'url': url,
        'headers': headers,
        'params': params,
        'timeout': REQUEST_TIMEOUT,
    }

    if method in ('POST', 'PUT', 'PATCH') and body:
        if body_type == 'json':
            headers.setdefault('Content-Type', 'application/json')
            request_kwargs['data'] = body
        elif body_type == 'form':
            form_data = {}
            try:
                pairs = json.loads(body) if isinstance(body, str) else body
                if isinstance(pairs, list):
                    for pair in pairs:
                        key = pair.get('key', '').strip()
                        if key:
                            form_data[key] = pair.get('value', '')
                elif isinstance(pairs, dict):
                    form_data = pairs
            except (json.JSONDecodeError, AttributeError):
                form_data = {}
            request_kwargs['data'] = form_data
        else:
            headers.setdefault('Content-Type', 'text/plain')
            request_kwargs['data'] = body

    try:
        start = time.time()
        resp = http_requests.request(**request_kwargs)
        duration_ms = round((time.time() - start) * 1000, 2)

        response_body = resp.text
        size_bytes = len(resp.content)

        response_headers = dict(resp.headers)

        result = {
            'status_code': resp.status_code,
            'headers': response_headers,
            'body': response_body,
            'duration_ms': duration_ms,
            'size_bytes': size_bytes,
        }

        database.add_history(data, result)

        return jsonify(result)

    except http_requests.exceptions.Timeout:
        return jsonify({'error': f'Request timed out after {REQUEST_TIMEOUT}s'}), 504
    except http_requests.exceptions.ConnectionError as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 502
    except http_requests.exceptions.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 500


@app.route('/api/collections', methods=['GET'])
def list_collections():
    collections = database.get_collections()
    for c in collections:
        try:
            c['headers'] = json.loads(c.get('headers_json', '[]'))
        except (json.JSONDecodeError, TypeError):
            c['headers'] = []
        try:
            c['params'] = json.loads(c.get('params_json', '[]'))
        except (json.JSONDecodeError, TypeError):
            c['params'] = []
    return jsonify(collections)


@app.route('/api/collections', methods=['POST'])
def create_collection():
    data = request.get_json()
    if not data or not data.get('collection_name') or not data.get('request_name'):
        return jsonify({'error': 'collection_name and request_name are required'}), 400
    if not data.get('method') or not data.get('url'):
        return jsonify({'error': 'method and url are required'}), 400

    item_id = database.save_to_collection(data)
    return jsonify({'id': item_id, 'message': 'Saved'}), 201


@app.route('/api/collections/<int:item_id>', methods=['DELETE'])
def delete_collection(item_id):
    deleted = database.delete_collection_item(item_id)
    if not deleted:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'message': 'Deleted'})


@app.route('/api/history', methods=['GET'])
def list_history():
    history = database.get_history()
    for h in history:
        try:
            h['headers'] = json.loads(h.get('headers_json', '[]'))
        except (json.JSONDecodeError, TypeError):
            h['headers'] = []
        try:
            h['params'] = json.loads(h.get('params_json', '[]'))
        except (json.JSONDecodeError, TypeError):
            h['params'] = []
        try:
            h['response_headers'] = json.loads(h.get('response_headers_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            h['response_headers'] = {}
    return jsonify(history)


@app.route('/api/history', methods=['DELETE'])
def clear_history():
    database.clear_history()
    return jsonify({'message': 'History cleared'})


@app.route('/api/environments', methods=['GET'])
def list_environments():
    envs = database.get_environments()
    for e in envs:
        e['variables'] = json.loads(e.get('variables_json', '{}'))
    return jsonify(envs)


@app.route('/api/environments', methods=['POST'])
def create_environment():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'name is required'}), 400

    variables = data.get('variables', {})
    if not isinstance(variables, dict):
        return jsonify({'error': 'variables must be an object'}), 400

    database.save_environment(data)
    return jsonify({'message': 'Saved'}), 201


@app.route('/api/environments/<int:env_id>', methods=['DELETE'])
def delete_environment(env_id):
    deleted = database.delete_environment(env_id)
    if not deleted:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'message': 'Deleted'})


if __name__ == '__main__':
    database.init_db()
    app.run(host='0.0.0.0', port=5111, debug=True)
