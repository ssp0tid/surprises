import re

from flask import Flask, jsonify, render_template, request

from color_engine import (
    contrast_ratio,
    generate_harmony,
    hex_to_hsl,
    hex_to_rgb,
    random_color,
    wcag_rating,
)
from database import delete_palette, init_db, list_palettes, save_palette

app = Flask(__name__)

HEX_PATTERN = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _normalize_hex(value: str) -> str:
    value = value.strip().lstrip("#")
    if not HEX_PATTERN.match(value):
        raise ValueError(f"Invalid hex color: '{value}'")
    return f"#{value.lower()}"


def _success(data):
    return jsonify({"success": True, "data": data})


def _error(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


# --- Pages ---


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/saved")
def saved():
    return render_template("saved.html")


# --- API ---


@app.route("/api/harmony")
def api_harmony():
    base = request.args.get("base")
    rule = request.args.get("rule")
    if not base:
        return _error("Missing 'base' parameter. Usage: /api/harmony?base=ff5500&rule=complementary")
    if not rule:
        return _error("Missing 'rule' parameter. Usage: /api/harmony?base=ff5500&rule=complementary")
    try:
        base_hex = _normalize_hex(base)
        colors = generate_harmony(base_hex, rule)
        return _success({"base": base_hex, "rule": rule, "colors": colors})
    except ValueError as e:
        return _error(str(e))


@app.route("/api/contrast")
def api_contrast():
    color1 = request.args.get("color1")
    color2 = request.args.get("color2")
    if not color1 or not color2:
        return _error("Missing parameters. Usage: /api/contrast?color1=ffffff&color2=000000")
    try:
        c1 = _normalize_hex(color1)
        c2 = _normalize_hex(color2)
        ratio = contrast_ratio(c1, c2)
        rating = wcag_rating(ratio)
        return _success({"color1": c1, "color2": c2, "ratio": ratio, "rating": rating})
    except ValueError as e:
        return _error(str(e))


@app.route("/api/random")
def api_random():
    color = random_color()
    h, s, lightness = hex_to_hsl(color)
    r, g, b = hex_to_rgb(color)
    return _success({
        "hex": color,
        "rgb": {"r": r, "g": g, "b": b},
        "hsl": {"h": h, "s": s, "l": lightness},
    })


@app.route("/api/palette/save", methods=["POST"])
def api_save_palette():
    data = request.get_json(silent=True)
    if not data:
        return _error("Request body must be JSON with 'name' and 'colors' fields.")
    name = data.get("name", "").strip()
    colors = data.get("colors")
    if not name:
        return _error("Palette 'name' is required.")
    if not colors or not isinstance(colors, list):
        return _error("'colors' must be a non-empty list of hex color strings.")
    try:
        normalized = [_normalize_hex(c) for c in colors]
    except ValueError as e:
        return _error(str(e))
    try:
        palette_id = save_palette(name, normalized)
        return _success({"id": palette_id, "name": name, "colors": normalized})
    except Exception:
        return _error("Failed to save palette. Please try again.", 500)


@app.route("/api/palette/list")
def api_list_palettes():
    try:
        palettes = list_palettes()
        return _success(palettes)
    except Exception:
        return _error("Failed to retrieve palettes.", 500)


@app.route("/api/palette/<int:palette_id>", methods=["DELETE"])
def api_delete_palette(palette_id: int):
    try:
        deleted = delete_palette(palette_id)
        if not deleted:
            return _error(f"Palette with id {palette_id} not found.", 404)
        return _success({"deleted": palette_id})
    except Exception:
        return _error("Failed to delete palette.", 500)


@app.route("/api/export")
def api_export():
    colors_param = request.args.get("colors")
    fmt = request.args.get("format", "css").lower()
    if not colors_param:
        return _error("Missing 'colors' parameter. Provide comma-separated hex values.")
    if fmt not in ("css", "scss", "tailwind"):
        return _error("Invalid format. Supported: css, scss, tailwind")
    try:
        colors = [_normalize_hex(c.strip()) for c in colors_param.split(",")]
    except ValueError as e:
        return _error(str(e))

    if fmt == "css":
        lines = [f"  --color-{i + 1}: {c};" for i, c in enumerate(colors)]
        output = ":root {\n" + "\n".join(lines) + "\n}"
    elif fmt == "scss":
        lines = [f"$color-{i + 1}: {c};" for i, c in enumerate(colors)]
        output = "\n".join(lines)
    else:
        entries = [f'    {(i + 1) * 100}: \'{c}\'' for i, c in enumerate(colors)]
        output = "colors: {\n  palette: {\n" + ",\n".join(entries) + "\n  }\n}"

    return _success({"format": fmt, "output": output})


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
