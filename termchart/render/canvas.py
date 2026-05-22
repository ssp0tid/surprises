from __future__ import annotations

# Braille dot bit offsets per (col, row) within a 2x4 character cell:
#   (0,0) (1,0)
#   (0,1) (1,1)
#   (0,2) (1,2)
#   (0,3) (1,3)
_DOT_MAP = {
    (0, 0): 0x01,
    (1, 0): 0x08,
    (0, 1): 0x02,
    (1, 1): 0x10,
    (0, 2): 0x04,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}

_BRAILLE_BASE = 0x2800


class BrailleCanvas:
    """A pixel-addressable canvas that renders to Braille Unicode characters.

    Args:
        width: Width in terminal character columns.
        height: Height in terminal character rows.
    """

    def __init__(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Canvas dimensions must be positive, got {width}x{height}")
        self.char_width = width
        self.char_height = height
        self.pixel_width = width * 2
        self.pixel_height = height * 4
        self._grid: list[list[int]] = [
            [0] * width for _ in range(height)
        ]

    def set_pixel(self, x: int, y: int) -> None:
        """Set a pixel at the given coordinates.

        Origin (0, 0) is top-left. X increases right, Y increases down.

        Args:
            x: Horizontal pixel coordinate (0 to pixel_width-1).
            y: Vertical pixel coordinate (0 to pixel_height-1).
        """
        if x < 0 or x >= self.pixel_width or y < 0 or y >= self.pixel_height:
            return
        char_col = x // 2
        char_row = y // 4
        dot_x = x % 2
        dot_y = y % 4
        self._grid[char_row][char_col] |= _DOT_MAP[(dot_x, dot_y)]

    def get_pixel(self, x: int, y: int) -> bool:
        """Check if a pixel is set at the given coordinates.

        Args:
            x: Horizontal pixel coordinate.
            y: Vertical pixel coordinate.

        Returns:
            True if the pixel is set.
        """
        if x < 0 or x >= self.pixel_width or y < 0 or y >= self.pixel_height:
            return False
        char_col = x // 2
        char_row = y // 4
        dot_x = x % 2
        dot_y = y % 4
        return bool(self._grid[char_row][char_col] & _DOT_MAP[(dot_x, dot_y)])

    def draw_line(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """Draw a line between two points using Bresenham's algorithm.

        Args:
            x0: Start X coordinate.
            y0: Start Y coordinate.
            x1: End X coordinate.
            y1: End Y coordinate.
        """
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            self.set_pixel(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def render(self) -> str:
        """Convert the canvas to a multi-line string of Braille characters.

        Returns:
            String with one line per character row.
        """
        lines: list[str] = []
        for row in self._grid:
            line = "".join(chr(_BRAILLE_BASE + cell) for cell in row)
            lines.append(line)
        return "\n".join(lines)
