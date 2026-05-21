import curses
import random
import time
import json
import os

from pieces import PIECES, COLORS, PIECE_NAMES
from board import Board

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")
LINE_SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}
INITIAL_SPEED = 0.5
SPEED_FACTOR = 0.05


class Game:
    MIN_HEIGHT = 24
    MIN_WIDTH = 40

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.board = Board()
        self.current_piece = None
        self.next_piece = None
        self.piece_x = 0
        self.piece_y = 0
        self.rotation = 0
        self.score = 0
        self.level = 1
        self.lines = 0
        self.paused = False
        self.game_over = False
        self.quit = False
        self.bag = []
        self._init_colors()
        self._spawn_piece()
        self.next_piece = self._next_from_bag()

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)
        curses.init_pair(4, curses.COLOR_GREEN, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.init_pair(7, curses.COLOR_WHITE, -1)
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_WHITE)

    def _next_from_bag(self):
        if not self.bag:
            self.bag = list(PIECE_NAMES)
            random.shuffle(self.bag)
        return self.bag.pop()

    def _spawn_piece(self):
        if self.next_piece:
            self.current_piece = self.next_piece
        else:
            self.current_piece = self._next_from_bag()
        self.next_piece = self._next_from_bag()
        self.rotation = 0
        self.piece_x = Board.WIDTH // 2 - 1
        self.piece_y = 0
        if not self.board.is_valid_position(self._get_cells()):
            self.game_over = True

    def _get_cells(self, piece=None, rotation=None, px=None, py=None):
        p = piece or self.current_piece
        r = rotation if rotation is not None else self.rotation
        x = px if px is not None else self.piece_x
        y = py if py is not None else self.piece_y
        return [(y + row, x + col) for row, col in PIECES[p][r]]

    def _try_rotate(self, direction):
        new_rot = (self.rotation + direction) % len(PIECES[self.current_piece])
        cells = self._get_cells(rotation=new_rot)
        if self.board.is_valid_position(cells):
            self.rotation = new_rot
            return
        # Wall kick: try left, right, up offsets
        for dx, dy in [(-1, 0), (1, 0), (0, -1)]:
            cells = self._get_cells(rotation=new_rot, px=self.piece_x + dx, py=self.piece_y + dy)
            if self.board.is_valid_position(cells):
                self.piece_x += dx
                self.piece_y += dy
                self.rotation = new_rot
                return

    def _move(self, dx, dy):
        cells = self._get_cells(px=self.piece_x + dx, py=self.piece_y + dy)
        if self.board.is_valid_position(cells):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False

    def _hard_drop(self):
        while self._move(0, 1):
            self.score += 2
        self._lock()

    def _lock(self):
        cells = self._get_cells()
        color = COLORS[self.current_piece]
        self.board.lock_piece(cells, color)
        cleared = self.board.clear_lines()
        self.lines += cleared
        self.score += LINE_SCORES.get(cleared, 0) * self.level
        self.level = self.lines // 10 + 1
        self._spawn_piece()

    def _get_ghost_y(self):
        gy = self.piece_y
        while True:
            cells = self._get_cells(py=gy + 1)
            if not self.board.is_valid_position(cells):
                return gy
            gy += 1

    def _get_speed(self):
        speed = INITIAL_SPEED - (self.level - 1) * SPEED_FACTOR
        return max(speed, 0.05)

    def handle_input(self, key):
        if key == ord('q'):
            self.quit = True
            self.game_over = True
            return
        if key == ord('p'):
            self.paused = not self.paused
            return
        if self.paused:
            return
        if key == curses.KEY_LEFT:
            self._move(-1, 0)
        elif key == curses.KEY_RIGHT:
            self._move(1, 0)
        elif key == curses.KEY_DOWN:
            if self._move(0, 1):
                self.score += 1
        elif key == curses.KEY_UP or key == ord('z'):
            self._try_rotate(1)
        elif key == ord('x'):
            self._try_rotate(-1)
        elif key == ord(' '):
            self._hard_drop()

    def draw(self):
        self.stdscr.clear()
        board_left = 2
        board_top = 1

        # Draw border
        for y in range(Board.HEIGHT + 1):
            self.stdscr.addstr(board_top + y, board_left - 1, "|")
            self.stdscr.addstr(board_top + y, board_left + Board.WIDTH * 2, "|")
        self.stdscr.addstr(board_top + Board.HEIGHT, board_left - 1, "+" + "-" * (Board.WIDTH * 2) + "+")

        # Draw board cells
        for y in range(Board.HEIGHT):
            for x in range(Board.WIDTH):
                cell = self.board.grid[y][x]
                if cell != 0:
                    self.stdscr.addstr(
                        board_top + y, board_left + x * 2,
                        "[]", curses.color_pair(cell) | curses.A_BOLD
                    )

        # Draw ghost piece
        ghost_y = self._get_ghost_y()
        if ghost_y != self.piece_y:
            ghost_cells = self._get_cells(py=ghost_y)
            for row, col in ghost_cells:
                if 0 <= row < Board.HEIGHT and 0 <= col < Board.WIDTH:
                    if self.board.grid[row][col] == 0:
                        self.stdscr.addstr(
                            board_top + row, board_left + col * 2,
                            "..", curses.A_DIM
                        )

        # Draw current piece
        cells = self._get_cells()
        color = COLORS[self.current_piece]
        for row, col in cells:
            if 0 <= row < Board.HEIGHT and 0 <= col < Board.WIDTH:
                self.stdscr.addstr(
                    board_top + row, board_left + col * 2,
                    "[]", curses.color_pair(color) | curses.A_BOLD
                )

        # Side panel
        panel_x = board_left + Board.WIDTH * 2 + 3
        self.stdscr.addstr(board_top, panel_x, f"Score: {self.score}")
        self.stdscr.addstr(board_top + 1, panel_x, f"Level: {self.level}")
        self.stdscr.addstr(board_top + 2, panel_x, f"Lines: {self.lines}")

        # Next piece preview
        self.stdscr.addstr(board_top + 4, panel_x, "Next:")
        next_cells = PIECES[self.next_piece][0]
        next_color = COLORS[self.next_piece]
        for row, col in next_cells:
            self.stdscr.addstr(
                board_top + 5 + row, panel_x + col * 2,
                "[]", curses.color_pair(next_color) | curses.A_BOLD
            )

        # Controls hint
        self.stdscr.addstr(board_top + 10, panel_x, "Controls:")
        self.stdscr.addstr(board_top + 11, panel_x, "Arrows:Move")
        self.stdscr.addstr(board_top + 12, panel_x, "Up/Z: Rotate")
        self.stdscr.addstr(board_top + 13, panel_x, "Space: Drop")
        self.stdscr.addstr(board_top + 14, panel_x, "P: Pause")
        self.stdscr.addstr(board_top + 15, panel_x, "Q: Quit")

        if self.paused:
            self.stdscr.addstr(board_top + 8, panel_x, "** PAUSED **", curses.A_BLINK)

        self.stdscr.refresh()

    def run(self):
        self.stdscr.nodelay(False)
        curses.curs_set(0)
        h, w = self.stdscr.getmaxyx()
        if h < self.MIN_HEIGHT or w < self.MIN_WIDTH:
            self.stdscr.addstr(0, 0, f"Terminal too small ({w}x{h}). Need {self.MIN_WIDTH}x{self.MIN_HEIGHT}.")
            self.stdscr.addstr(1, 0, "Resize and restart.")
            self.stdscr.refresh()
            self.stdscr.getch()
            return
        self._show_title()
        self.stdscr.nodelay(True)
        last_drop = time.time()

        while not self.game_over:
            key = self.stdscr.getch()
            if key != -1:
                self.handle_input(key)

            if not self.paused and not self.game_over:
                now = time.time()
                if now - last_drop >= self._get_speed():
                    if not self._move(0, 1):
                        self._lock()
                    last_drop = now

            if not self.game_over:
                try:
                    self.draw()
                except curses.error:
                    pass
            time.sleep(0.016)

        if not self.quit:
            self._show_game_over()

    def _show_title(self):
        self.stdscr.clear()
        title = [
            "╔════════════════════╗",
            "║   TETRIS TERMINAL  ║",
            "╚════════════════════╝",
        ]
        h, w = self.stdscr.getmaxyx()
        start_y = h // 2 - 3
        for i, line in enumerate(title):
            x = max(0, w // 2 - len(line) // 2)
            self.stdscr.addstr(start_y + i, x, line, curses.A_BOLD)
        self.stdscr.addstr(start_y + 4, w // 2 - 10, "Press any key to start")
        self.stdscr.refresh()
        self.stdscr.nodelay(False)
        self.stdscr.getch()

    def _show_game_over(self):
        self.stdscr.nodelay(False)
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        cy = h // 2 - 4
        cx = w // 2

        self.stdscr.addstr(cy, cx - 5, "GAME OVER", curses.A_BOLD)
        self.stdscr.addstr(cy + 2, cx - 8, f"Final Score: {self.score}")
        self.stdscr.addstr(cy + 3, cx - 8, f"Level: {self.level}  Lines: {self.lines}")

        scores = self._load_scores()
        scores.append(self.score)
        scores = sorted(scores, reverse=True)[:5]
        self._save_scores(scores)

        self.stdscr.addstr(cy + 5, cx - 8, "HIGH SCORES:")
        marked = False
        for i, s in enumerate(scores):
            marker = ""
            if not marked and s == self.score:
                marker = " <-"
                marked = True
            self.stdscr.addstr(cy + 6 + i, cx - 8, f"  {i+1}. {s}{marker}")

        self.stdscr.addstr(cy + 12, cx - 10, "Press any key to exit")
        self.stdscr.refresh()
        self.stdscr.getch()

    def _load_scores(self):
        try:
            with open(SCORES_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            return [s for s in data if isinstance(s, (int, float))]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def _save_scores(self, scores):
        try:
            with open(SCORES_FILE, "w") as f:
                json.dump(scores, f)
        except OSError:
            pass


def game_main(stdscr):
    game = Game(stdscr)
    game.run()


def main():
    curses.wrapper(game_main)


if __name__ == "__main__":
    main()
