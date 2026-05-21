"""Curses-based maze rendering engine with box-drawing characters."""

import curses
import time

N, E, S, W = 1, 2, 4, 8


COLOR_WALL = 1
COLOR_PATH = 2
COLOR_PLAYER = 3
COLOR_VISITED = 4
COLOR_MARKER = 5


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_WALL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_PATH, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_PLAYER, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_VISITED, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_MARKER, curses.COLOR_CYAN, -1)


class MazeRenderer:
    def __init__(self, stdscr, maze, cell_width=3, cell_height=1):
        self.stdscr = stdscr
        self.maze = maze
        self.height = len(maze)
        self.width = len(maze[0])
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.screen_rows = self.height * (cell_height + 1) + 1
        self.screen_cols = self.width * (cell_width + 1) + 1
        init_colors()

    def check_terminal_size(self):
        max_y, max_x = self.stdscr.getmaxyx()
        if max_y < self.screen_rows + 2 or max_x < self.screen_cols:
            return False
        return True

    def draw_maze(self):
        self.stdscr.clear()
        cw = self.cell_width
        ch = self.cell_height
        color = curses.color_pair(COLOR_WALL)

        for row in range(self.height):
            for col in range(self.width):
                cell = self.maze[row][col]
                sy = row * (ch + 1)
                sx = col * (cw + 1)

                # Top-left corner
                self._draw_corner(row, col, sy, sx, color)

                # North wall
                if cell & N:
                    for i in range(1, cw + 1):
                        self._addch(sy, sx + i, "─", color)
                else:
                    for i in range(1, cw + 1):
                        self._addch(sy, sx + i, " ", color)

                # West wall
                if cell & W:
                    for i in range(1, ch + 1):
                        self._addch(sy + i, sx, "│", color)
                else:
                    for i in range(1, ch + 1):
                        self._addch(sy + i, sx, " ", color)

        # Right border
        for row in range(self.height):
            cell = self.maze[row][self.width - 1]
            sy = row * (ch + 1)
            sx = self.width * (cw + 1)
            self._draw_right_border_corner(row, sy, sx, color)
            if cell & E:
                for i in range(1, ch + 1):
                    self._addch(sy + i, sx, "│", color)
            else:
                for i in range(1, ch + 1):
                    self._addch(sy + i, sx, " ", color)

        # Bottom border
        for col in range(self.width):
            cell = self.maze[self.height - 1][col]
            sy = self.height * (ch + 1)
            sx = col * (cw + 1)
            self._draw_bottom_border_corner(col, sy, sx, color)
            if cell & S:
                for i in range(1, cw + 1):
                    self._addch(sy, sx + i, "─", color)
            else:
                for i in range(1, cw + 1):
                    self._addch(sy, sx + i, " ", color)

        # Bottom-right corner
        sy = self.height * (ch + 1)
        sx = self.width * (cw + 1)
        self._addch(sy, sx, "┘", color)

        self.stdscr.refresh()

    def _draw_corner(self, row, col, sy, sx, color):
        has_n = row > 0 and (self.maze[row - 1][col] & W or (col > 0 and self.maze[row - 1][col - 1] & E))
        has_s = self.maze[row][col] & W or (col > 0 and self.maze[row][col - 1] & E)
        has_w = col > 0 and (self.maze[row][col - 1] & N or (row > 0 and self.maze[row - 1][col - 1] & S))
        has_e = self.maze[row][col] & N or (row > 0 and self.maze[row - 1][col] & S)

        ch = self._pick_corner(
            up=has_n or (row > 0),
            down=has_s or True,
            left=has_w or (col > 0),
            right=has_e or True,
            row=row, col=col
        )
        self._addch(sy, sx, ch, color)

    def _draw_right_border_corner(self, row, sy, sx, color):
        ch = "┤" if row == 0 else "┤"
        if row == 0:
            has_down = self.maze[row][self.width - 1] & E
            ch = "┐" if has_down else "╴"
        else:
            ch = "┤"
        self._addch(sy, sx, ch, color)

    def _draw_bottom_border_corner(self, col, sy, sx, color):
        if col == 0:
            self._addch(sy, sx, "└", color)
        else:
            self._addch(sy, sx, "┴", color)

    def _pick_corner(self, up, down, left, right, row, col):
        if row == 0 and col == 0:
            return "┌"
        if row == 0:
            return "┬"
        if col == 0:
            return "├"
        return "┼"

    def _addch(self, y, x, ch, attr=0):
        """Write a character at (y, x). Silently ignores out-of-bounds writes
        and curses errors — this is intentional since terminal resizes can
        happen mid-draw and we don't want to crash on partial renders."""
        max_y, max_x = self.stdscr.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x - 1:
            try:
                self.stdscr.addstr(y, x, ch, attr)
            except curses.error:
                pass

    def highlight_cell(self, row, col, color_pair):
        ch = self.cell_height
        cw = self.cell_width
        sy = row * (ch + 1) + 1
        sx = col * (cw + 1) + 1
        attr = curses.color_pair(color_pair)
        for dy in range(ch):
            for dx in range(cw):
                self._addch(sy + dy, sx + dx, " ", attr | curses.A_REVERSE)

    def draw_path(self, path, color_pair):
        for row, col in path:
            self.highlight_cell(row, col, color_pair)
        self.stdscr.refresh()

    def draw_status(self, message):
        max_y, max_x = self.stdscr.getmaxyx()
        status_y = self.screen_rows + 1
        if status_y < max_y:
            self.stdscr.move(status_y, 0)
            self.stdscr.clrtoeol()
            self.stdscr.addnstr(status_y, 0, message, max_x - 1)
            self.stdscr.refresh()

    def animate_solve(self, solver_generator, speed=0.05):
        self.stdscr.nodelay(True)
        final_path = []

        for visited, path in solver_generator:
            try:
                key = self.stdscr.getch()
                if key == ord("q"):
                    self.stdscr.nodelay(False)
                    return path
            except curses.error:
                pass

            self.draw_maze()

            for r, c in visited:
                self.highlight_cell(r, c, COLOR_VISITED)

            if path:
                for r, c in path:
                    self.highlight_cell(r, c, COLOR_PATH)
                final_path = path

            self.highlight_cell(0, 0, COLOR_MARKER)
            self.highlight_cell(self.height - 1, self.width - 1, COLOR_MARKER)

            self.draw_status(f"Solving... visited: {len(visited)} | Press Q to skip")
            self.stdscr.refresh()
            time.sleep(speed)

        self.stdscr.nodelay(False)
        return final_path
