from __future__ import annotations

from render.canvas import BrailleCanvas
from render.colors import DEFAULT_SCHEME


class ScatterChart:
    def render(self, x: list[float], y: list[float], width: int = 60, height: int = 20,
               color_scheme: str = DEFAULT_SCHEME, color_enabled: bool = True) -> str:
        if not x or not y or len(x) != len(y):
            return ""

        x_min, x_max = min(x), max(x)
        y_min, y_max = min(y), max(y)

        if x_min == x_max:
            x_max = x_min + 1
        if y_min == y_max:
            y_max = y_min + 1

        y_axis_width = max(len(f"{y_min:.1f}"), len(f"{y_max:.1f}")) + 1
        canvas_width = width - y_axis_width - 1
        if canvas_width <= 0:
            return ""
        canvas_height = height

        canvas = BrailleCanvas(canvas_width, canvas_height)

        for xi, yi in zip(x, y):
            px = int(((xi - x_min) / (x_max - x_min)) * (canvas.pixel_width - 1))
            py = int((1 - (yi - y_min) / (y_max - y_min)) * (canvas.pixel_height - 1))
            canvas.set_pixel(px, py)

        rendered = canvas.render()
        canvas_lines = rendered.split("\n")

        lines: list[str] = []
        for i, canvas_line in enumerate(canvas_lines):
            if i == 0:
                label = f"{y_max:.1f}".rjust(y_axis_width)
            elif i == len(canvas_lines) - 1:
                label = f"{y_min:.1f}".rjust(y_axis_width)
            elif i == len(canvas_lines) // 2:
                mid = (y_max + y_min) / 2
                label = f"{mid:.1f}".rjust(y_axis_width)
            else:
                label = " " * y_axis_width
            lines.append(f"{label}│{canvas_line}")

        axis_line = " " * y_axis_width + "└" + "─" * canvas_width
        lines.append(axis_line)

        first = f"{x_min:.1f}"
        last = f"{x_max:.1f}"
        spacing = canvas_width - len(first) - len(last)
        x_label_line = " " * (y_axis_width + 1) + first + " " * max(spacing, 1) + last
        lines.append(x_label_line)

        return "\n".join(lines)
