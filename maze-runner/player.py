"""Playable maze mode with keyboard input, movement, and win detection."""

import curses
import time

from renderer import MazeRenderer, COLOR_PLAYER, COLOR_MARKER, COLOR_PATH

N, E, S, W = 1, 2, 4, 8


class PlayerMode:
    def __init__(self, stdscr, maze, width, height):
        self.stdscr = stdscr
        self.maze = maze
        self.width = width
        self.height = height
        self.player_row = 0
        self.player_col = 0
        self.moves = 0
        self.renderer = MazeRenderer(stdscr, maze)
        self.trail = [(0, 0)]

    def run(self):
        """Main game loop. Returns elapsed time in seconds on win, or None if quit."""
        self.stdscr.nodelay(False)
        curses.curs_set(0)

        if not self.renderer.check_terminal_size():
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, "Terminal too small! Resize and try again.")
            self.stdscr.addstr(1, 0, f"Need: {self.renderer.screen_cols}x{self.renderer.screen_rows + 2}")
            self.stdscr.addstr(2, 0, "Press any key to exit.")
            self.stdscr.getch()
            return None

        start_time = time.time()

        while True:
            self.renderer.draw_maze()
            self._draw_trail()
            self.renderer.highlight_cell(0, 0, COLOR_MARKER)
            self.renderer.highlight_cell(self.height - 1, self.width - 1, COLOR_MARKER)
            self.renderer.highlight_cell(self.player_row, self.player_col, COLOR_PLAYER)

            elapsed = time.time() - start_time
            self.renderer.draw_status(
                f"Time: {elapsed:.1f}s | Moves: {self.moves} | "
                f"Arrow keys/WASD to move | Q to quit"
            )

            key = self.stdscr.getch()
            direction = self._key_to_direction(key)

            if key == ord("q") or key == ord("Q"):
                return None

            if direction and self.can_move(direction):
                self.move(direction)

                if self.check_win():
                    elapsed = time.time() - start_time
                    self.renderer.draw_maze()
                    self._draw_trail()
                    self.renderer.highlight_cell(self.player_row, self.player_col, COLOR_PLAYER)
                    self.renderer.draw_status(
                        f"YOU WIN! Time: {elapsed:.1f}s | Moves: {self.moves} | Press any key"
                    )
                    self.stdscr.getch()
                    return elapsed

    def can_move(self, direction):
        return not (self.maze[self.player_row][self.player_col] & direction)

    def move(self, direction):
        dx = {N: -1, E: 0, S: 1, W: 0}
        dy = {N: 0, E: 1, S: 0, W: -1}
        self.player_row += dx[direction]
        self.player_col += dy[direction]
        self.moves += 1
        self.trail.append((self.player_row, self.player_col))

    def check_win(self):
        return self.player_row == self.height - 1 and self.player_col == self.width - 1

    def _key_to_direction(self, key):
        mapping = {
            curses.KEY_UP: N, ord("w"): N, ord("W"): N,
            curses.KEY_RIGHT: E, ord("d"): E, ord("D"): E,
            curses.KEY_DOWN: S, ord("s"): S, ord("S"): S,
            curses.KEY_LEFT: W, ord("a"): W, ord("A"): W,
        }
        return mapping.get(key)

    def _draw_trail(self):
        for r, c in self.trail[:-1]:
            self.renderer.highlight_cell(r, c, COLOR_PATH)
