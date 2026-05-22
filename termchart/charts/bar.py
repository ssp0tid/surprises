from __future__ import annotations

from render.colors import colorize, gradient, DEFAULT_SCHEME


_HBAR_BLOCKS = " ▏▎▍▌▋▊▉█"
_VBAR_BLOCKS = " ▁▂▃▄▅▆▇█"


class HBarChart:
    def render(self, data: list[dict], width: int = 40, color_scheme: str = DEFAULT_SCHEME,
               sort: bool = False, show_values: bool = True, color_enabled: bool = True) -> str:
        if not data:
            return ""

        items = [(d.get("label", ""), float(d.get("value", 0))) for d in data]
        if sort:
            items.sort(key=lambda x: x[1], reverse=True)

        max_val = max(v for _, v in items)
        min_val = min(v for _, v in items)
        max_label_len = max(len(lbl) for lbl, _ in items)

        bar_width = width - max_label_len - 2
        if show_values:
            max_val_str_len = max(len(f"{v:g}") for _, v in items)
            bar_width -= max_val_str_len + 1

        bar_width = max(bar_width, 10)
        lines: list[str] = []

        for i, (label, value) in enumerate(items):
            if max_val == 0:
                filled = 0.0
            else:
                filled = (value / max_val) * bar_width

            full_blocks = int(filled)
            remainder = filled - full_blocks
            partial_index = int(remainder * 8)

            bar = "█" * full_blocks
            if partial_index > 0 and full_blocks < bar_width:
                bar += _HBAR_BLOCKS[partial_index]

            color_idx = gradient(value, min_val, max_val, color_scheme, color_enabled)
            colored_bar = colorize(bar, color_idx, color_enabled)

            padded_label = label.rjust(max_label_len)
            line = f"{padded_label} │{colored_bar}"
            if show_values:
                line += f" {value:g}"
            lines.append(line)

        return "\n".join(lines)


class VBarChart:
    def render(self, data: list[dict], height: int = 20, color_scheme: str = DEFAULT_SCHEME,
               sort: bool = False, color_enabled: bool = True) -> str:
        if not data:
            return ""

        items = [(d.get("label", ""), float(d.get("value", 0))) for d in data]
        if sort:
            items.sort(key=lambda x: x[1], reverse=True)

        max_val = max(v for _, v in items)
        min_val = min(v for _, v in items)

        if max_val == 0:
            # All values are zero — render empty bars with labels only
            labels = " ".join(lbl[:1] if len(lbl) > 1 else lbl for _, (lbl, _) in enumerate(items))
            return labels

        lines: list[str] = []

        for row in range(height, 0, -1):
            threshold = (row / height) * max_val
            line_chars: list[str] = []
            for i, (label, value) in enumerate(items):
                if value >= threshold:
                    level = min(8, int(((value - threshold + (max_val / height)) / (max_val / height)) * 8))
                    char = _VBAR_BLOCKS[min(level, 8)]
                else:
                    prev_threshold = ((row - 1) / height) * max_val
                    if value > prev_threshold:
                        level = int(((value - prev_threshold) / (max_val / height)) * 8)
                        char = _VBAR_BLOCKS[min(level, 8)]
                    else:
                        char = " "

                color_idx = gradient(value, min_val, max_val, color_scheme, color_enabled)
                line_chars.append(colorize(char, color_idx, color_enabled))
            lines.append(" ".join(line_chars))

        labels = " ".join(lbl[:1] if len(lbl) > 1 else lbl for _, (lbl, _) in enumerate(items))
        lines.append(labels)

        return "\n".join(lines)
