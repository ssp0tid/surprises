import base64
import io
import json
import logging

from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image

from database import init_db, create_project, get_project, list_projects, update_project, delete_project

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB request size limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/projects", methods=["GET"])
def api_list_projects():
    projects = list_projects()
    return jsonify(projects)


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body required"}), 400

    name = body.get("name", "").strip()
    width = body.get("width")
    height = body.get("height")

    if not name:
        return jsonify({"error": "Project name is required"}), 400
    if not isinstance(width, int) or not isinstance(height, int):
        return jsonify({"error": "Width and height must be integers"}), 400
    if width not in (8, 16, 32, 64, 128) or height not in (8, 16, 32, 64, 128):
        return jsonify({"error": "Dimensions must be 8, 16, 32, 64, or 128"}), 400

    project_id = create_project(name, width, height)
    return jsonify({"id": project_id}), 201


@app.route("/api/projects/<int:pid>", methods=["GET"])
def api_get_project(pid):
    project = get_project(pid)
    if project is None:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project)


@app.route("/api/projects/<int:pid>", methods=["PUT"])
def api_update_project(pid):
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body required"}), 400

    data = body.get("data")
    if data is None:
        return jsonify({"error": "Project data is required"}), 400

    name = body.get("name")
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data)
    elif isinstance(data, str):
        try:
            json.loads(data)
            data_str = data
        except (json.JSONDecodeError, ValueError):
            return jsonify({"error": "Project data must be valid JSON"}), 400
    else:
        return jsonify({"error": "Project data must be a JSON object or string"}), 400

    if not update_project(pid, data_str, name):
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/projects/<int:pid>", methods=["DELETE"])
def api_delete_project(pid):
    if not delete_project(pid):
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/export/gif", methods=["POST"])
def api_export_gif():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body required"}), 400

    frames_data = body.get("frames", [])
    if not frames_data:
        return jsonify({"error": "No frames provided"}), 400
    if len(frames_data) > 64:
        return jsonify({"error": "Maximum 64 frames allowed"}), 400

    try:
        images = []
        durations = []

        for frame in frames_data:
            img_data = frame.get("data", "")
            duration = frame.get("duration", 100)

            if not img_data:
                return jsonify({"error": "Frame missing image data"}), 400

            if "," in img_data:
                img_data = img_data.split(",", 1)[1]

            raw = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(raw)).convert("RGBA")

            if img.width > 2048 or img.height > 2048:
                return jsonify({"error": "Frame dimensions exceed 2048x2048 limit"}), 400

            images.append(img)
            durations.append(max(16, min(5000, int(duration))))

        output = io.BytesIO()
        images[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=0,
            disposal=2
        )
        output.seek(0)

        return send_file(output, mimetype="image/gif", download_name="animation.gif")

    except (base64.binascii.Error, ValueError) as e:
        return jsonify({"error": f"Invalid frame data: {str(e)}"}), 400
    except Exception as e:
        logger.exception("GIF export failed")
        return jsonify({"error": "GIF export failed"}), 500


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise SystemExit(1)
    app.run(debug=True, port=5000)
