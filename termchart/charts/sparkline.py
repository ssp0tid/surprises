from __future__ import annotations

from render.colors import colorize, gradient, DEFAULT_SCHEME


_SPARK_BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float], color_enabled: bool = True,
              color_scheme: str = DEFAULT_SCHEME, show_minmax: bool = False) -> str:
    if not values:
        return ""

    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        bar_index = 4
        chars: list[str] = []
        for v in values:
            color_idx = gradient(v, min_val, max_val, color_scheme, color_enabled)
            chars.append(colorize(_SPARK_BLOCKS[bar_index], color_idx, color_enabled))
    else:
        chars = []
        for v in values:
            ratio = (v - min_val) / (max_val - min_val)
            bar_index = int(ratio * 7)
            bar_index = max(0, min(7, bar_index))
            color_idx = gradient(v, min_val, max_val, color_scheme, color_enabled)
            chars.append(colorize(_SPARK_BLOCKS[bar_index], color_idx, color_enabled))

    result = "".join(chars)

    if show_minmax:
        result = f"({min_val:g}) {result} ({max_val:g})"

    return result
