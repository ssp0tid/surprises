from __future__ import annotations

from render.canvas import BrailleCanvas
from render.colors import colorize, scheme_color, DEFAULT_SCHEME


class LineChart:
    def render(self, data: list[dict], width: int = 60, height: int = 20,
               y_columns: list[str] | None = None, color_scheme: str = DEFAULT_SCHEME,
               color_enabled: bool = True) -> str:
        if not data:
            return ""

        if y_columns is None:
            y_columns = ["value"]

        all_values: list[float] = []
        series_data: dict[str, list[float]] = {}
        for col in y_columns:
            values = [float(d.get(col, 0)) for d in data]
            series_data[col] = values
            all_values.extend(values)

        if not all_values:
            return ""

        y_min = min(all_values)
        y_max = max(all_values)
        if y_min == y_max:
            y_max = y_min + 1

        y_axis_width = max(len(f"{y_min:.1f}"), len(f"{y_max:.1f}")) + 1
        canvas_width = width - y_axis_width - 1
        if canvas_width <= 0:
            return ""
        canvas_height = height

        canvas = BrailleCanvas(canvas_width, canvas_height)

        for series_idx, (col, values) in enumerate(series_data.items()):
            n = len(values)
            for i in range(n - 1):
                x0 = int((i / max(n - 1, 1)) * (canvas.pixel_width - 1))
                x1 = int(((i + 1) / max(n - 1, 1)) * (canvas.pixel_width - 1))
                y0 = int((1 - (values[i] - y_min) / (y_max - y_min)) * (canvas.pixel_height - 1))
                y1 = int((1 - (values[i + 1] - y_min) / (y_max - y_min)) * (canvas.pixel_height - 1))
                canvas.draw_line(x0, y0, x1, y1)

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

        x_labels = [d.get("label", "") for d in data]
        if x_labels:
            axis_line = " " * y_axis_width + "└" + "─" * canvas_width
            lines.append(axis_line)

            first = x_labels[0][:y_axis_width] if x_labels else ""
            last = x_labels[-1][:y_axis_width] if x_labels else ""
            spacing = canvas_width - len(first) - len(last)
            x_label_line = " " * (y_axis_width + 1) + first + " " * max(spacing, 1) + last
            lines.append(x_label_line)

        if len(y_columns) > 1:
            legend_parts: list[str] = []
            for i, col in enumerate(y_columns):
                color_idx = scheme_color(i, color_scheme)
                legend_parts.append(colorize(f"● {col}", color_idx, color_enabled))
            lines.append(" " * (y_axis_width + 1) + "  ".join(legend_parts))

        return "\n".join(lines)
