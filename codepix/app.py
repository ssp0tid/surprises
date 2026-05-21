from flask import Flask, request, send_file, render_template
from pygments import highlight
from pygments.lexers import guess_lexer, TextLexer
from pygments.formatters import ImageFormatter
from pygments.styles import get_style_by_name
import io

app = Flask(__name__)

# Theme options shown to the user (display names). We map these to Pygments style names.
THEME_CHOICES = [
    "default",
    "Monokai",
    "Solarized Dark",
    "Solarized Light",
    "Dracula",
    "Github",
    "Colorful",
]


def style_name_from_display(display_name: str) -> str:
    mapping = {
        "default": "default",
        "Monokai": "monokai",
        "Solarized Dark": "solarized-dark",
        "Solarized Light": "solarized-light",
        "Dracula": "dracula",
        "Github": "github",
        "Colorful": "colorful",
    }
    return mapping.get(display_name, "default")


@app.route("/", methods=["GET"])
def index():
    # Render the UI with a code input, theme selector, and export button
    return render_template("index.html", themes=THEME_CHOICES)


@app.route("/export", methods=["POST"])
def export_png():
    code = request.form.get("code", "") or ""
    theme_display = request.form.get("theme", "default") or "default"

    # Resolve the style to use for Pygments ImageFormatter
    style_name = style_name_from_display(theme_display)
    try:
        style = get_style_by_name(style_name)
    except Exception:
        # Fallback to default if the style isn't found
        style = get_style_by_name("default")

    # Auto-detect language; fall back to plain text if detection fails
    try:
        lexer = guess_lexer(code)
    except Exception:
        lexer = TextLexer()

    # Render to PNG using PIL via Pygments' ImageFormatter
    formatter = ImageFormatter(
        style=style,
        font_name="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        line_numbers=False,
        font_size=18,
        image_format="PNG",
    )
    image_bytes = io.BytesIO()
    try:
        highlight(code, lexer, formatter, image_bytes)
        image_bytes.seek(0)
    except Exception as e:
        return f"Error generating image: {e}", 500

    # Send PNG as a downloadable attachment
    return send_file(
        image_bytes,
        mimetype="image/png",
        as_attachment=True,
        download_name="code.png",
    )


if __name__ == "__main__":
    app.run(debug=True)
