#!/usr/bin/env python3
"""diskvu — Interactive Terminal Disk Usage Analyzer."""

import argparse
import curses
import dataclasses
import os
import shutil
import threading
import time
from typing import Optional


@dataclasses.dataclass
class DirNode:
    """Represents a file or directory with recursive size info."""

    path: str
    name: str
    size: int
    is_dir: bool
    children: list
    file_count: int
    error: Optional[str] = None


def format_size(bytes_val: int) -> str:
    """Return human-readable size string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024**2:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024**3:
        return f"{bytes_val / 1024**2:.1f} MB"
    elif bytes_val < 1024**4:
        return f"{bytes_val / 1024**3:.1f} GB"
    else:
        return f"{bytes_val / 1024**4:.1f} TB"


def scan_directory(path: str, progress_callback=None) -> DirNode:
    """Recursively scan a directory and return a DirNode tree."""
    path = os.path.abspath(path)
    name = os.path.basename(path) or path

    if not os.path.isdir(path):
        try:
            size = os.path.getsize(path)
        except OSError as e:
            return DirNode(
                path=path, name=name, size=0, is_dir=False,
                children=[], file_count=1, error=str(e)
            )
        return DirNode(
            path=path, name=name, size=size, is_dir=False,
            children=[], file_count=1
        )

    children = []
    total_size = 0
    total_files = 0
    error_msg = None

    try:
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        child = scan_directory(entry.path, progress_callback)
                        children.append(child)
                        total_size += child.size
                        total_files += child.file_count
                    else:
                        try:
                            size = entry.stat(follow_symlinks=False).st_size
                        except OSError:
                            size = 0
                        children.append(DirNode(
                            path=entry.path, name=entry.name, size=size,
                            is_dir=False, children=[], file_count=1
                        ))
                        total_size += size
                        total_files += 1
                        if progress_callback:
                            progress_callback(total_files)
                except PermissionError as e:
                    children.append(DirNode(
                        path=entry.path, name=entry.name, size=0,
                        is_dir=entry.is_dir(follow_symlinks=False),
                        children=[], file_count=0, error=str(e)
                    ))
                except OSError as e:
                    children.append(DirNode(
                        path=entry.path, name=entry.name, size=0,
                        is_dir=False, children=[], file_count=0, error=str(e)
                    ))
    except PermissionError as e:
        error_msg = str(e)
    except OSError as e:
        error_msg = str(e)

    children.sort(key=lambda n: n.size, reverse=True)

    return DirNode(
        path=path, name=name, size=total_size, is_dir=True,
        children=children, file_count=total_files, error=error_msg
    )


class DiskVuApp:
    """Main curses application for disk usage exploration."""

    SORT_MODES = ["size_desc", "size_asc", "name_asc", "file_count"]
    SORT_LABELS = ["Size ↓", "Size ↑", "Name", "Files"]
    SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, root_path: str):
        self.root_path = os.path.abspath(root_path)
        self.current_node: Optional[DirNode] = None
        self.history: list[DirNode] = []
        self.cursor_pos = 0
        self.scroll_offset = 0
        self.sort_mode_idx = 0
        self.show_help = False
        self.scanning = False
        self.scan_file_count = 0
        self.spinner_idx = 0
        self.stdscr = None

    def run(self, stdscr):
        """Main entry point called by curses.wrapper."""
        self.stdscr = stdscr
        curses.curs_set(0)

        has_default_colors = False
        try:
            curses.use_default_colors()
            has_default_colors = True
        except curses.error:
            pass

        if curses.has_colors():
            bg = -1 if has_default_colors else curses.COLOR_BLACK
            curses.init_pair(1, curses.COLOR_CYAN, bg)
            curses.init_pair(2, curses.COLOR_GREEN, bg)
            curses.init_pair(3, curses.COLOR_YELLOW, bg)
            curses.init_pair(4, curses.COLOR_RED, bg)
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)

        self._scan(self.root_path)
        self._main_loop()

    def _scan(self, path: str):
        """Scan directory in background thread with progress."""
        self.scanning = True
        self.scan_file_count = 0
        scan_result: list = []

        def progress(count):
            self.scan_file_count = count

        def do_scan():
            node = scan_directory(path, progress)
            scan_result.append(node)
            self.scanning = False

        thread = threading.Thread(target=do_scan, daemon=True)
        thread.start()

        self.stdscr.timeout(100)
        while self.scanning:
            self._draw_scanning()
            key = self.stdscr.getch()
            if key == ord('q') or key == 27:
                raise SystemExit(0)
            self.spinner_idx = (self.spinner_idx + 1) % len(self.SPINNER)

        thread.join()
        self.stdscr.timeout(-1)

        if scan_result:
            self.current_node = scan_result[0]
            self.cursor_pos = 0
            self.scroll_offset = 0

    def _draw_scanning(self):
        """Draw scanning progress screen."""
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        spinner = self.SPINNER[self.spinner_idx]
        msg = f" {spinner} Scanning... [{self.scan_file_count} files found]"
        y = h // 2
        x = max(0, (w - len(msg)) // 2)
        try:
            self.stdscr.addstr(y, x, msg, curses.A_BOLD)
        except curses.error:
            pass
        self.stdscr.refresh()

    def _main_loop(self):
        """Main input loop."""
        while True:
            self._draw()
            key = self.stdscr.getch()

            if key == curses.KEY_RESIZE:
                continue

            if self.show_help:
                self.show_help = False
                continue

            if key in (ord('q'), 27):
                break
            elif key in (curses.KEY_UP, ord('k')):
                self._move_cursor(-1)
            elif key in (curses.KEY_DOWN, ord('j')):
                self._move_cursor(1)
            elif key in (curses.KEY_ENTER, 10, 13, curses.KEY_RIGHT, ord('l')):
                self._enter_dir()
            elif key in (curses.KEY_BACKSPACE, 127, curses.KEY_LEFT, ord('h')):
                self._go_parent()
            elif key == ord('s'):
                self._cycle_sort()
            elif key == ord('d'):
                self._delete_selected()
            elif key == ord('r'):
                self._rescan()
            elif key == ord('?'):
                self.show_help = True

    def _move_cursor(self, delta: int):
        """Move cursor up or down."""
        if not self.current_node or not self.current_node.children:
            return
        self.cursor_pos = max(0, min(
            len(self.current_node.children) - 1, self.cursor_pos + delta
        ))
        self._ensure_visible()

    def _ensure_visible(self):
        """Ensure cursor is within visible scroll area."""
        h, _ = self.stdscr.getmaxyx()
        content_height = h - 4
        if self.cursor_pos < self.scroll_offset:
            self.scroll_offset = self.cursor_pos
        elif self.cursor_pos >= self.scroll_offset + content_height:
            self.scroll_offset = self.cursor_pos - content_height + 1

    def _enter_dir(self):
        """Enter the selected directory."""
        if not self.current_node or not self.current_node.children:
            return
        selected = self.current_node.children[self.cursor_pos]
        if selected.is_dir and not selected.error:
            self.history.append(self.current_node)
            self.current_node = selected
            self.cursor_pos = 0
            self.scroll_offset = 0

    def _go_parent(self):
        """Navigate to parent directory."""
        if self.history:
            self.current_node = self.history.pop()
            self.cursor_pos = 0
            self.scroll_offset = 0

    def _cycle_sort(self):
        """Cycle through sort modes."""
        self.sort_mode_idx = (self.sort_mode_idx + 1) % len(self.SORT_MODES)
        self._apply_sort()

    def _apply_sort(self):
        """Apply current sort mode to children."""
        if not self.current_node:
            return
        mode = self.SORT_MODES[self.sort_mode_idx]
        if mode == "size_desc":
            self.current_node.children.sort(key=lambda n: n.size, reverse=True)
        elif mode == "size_asc":
            self.current_node.children.sort(key=lambda n: n.size)
        elif mode == "name_asc":
            self.current_node.children.sort(key=lambda n: n.name.lower())
        elif mode == "file_count":
            self.current_node.children.sort(key=lambda n: n.file_count, reverse=True)

    def _clamp_cursor(self):
        """Ensure cursor_pos is within valid bounds."""
        if not self.current_node or not self.current_node.children:
            self.cursor_pos = 0
            self.scroll_offset = 0
            return
        max_pos = len(self.current_node.children) - 1
        if self.cursor_pos > max_pos:
            self.cursor_pos = max_pos
        self._ensure_visible()

    def _delete_selected(self):
        """Delete selected item with confirmation."""
        if not self.current_node or not self.current_node.children:
            return
        selected = self.current_node.children[self.cursor_pos]
        h, w = self.stdscr.getmaxyx()

        prompt = f"Delete {selected.name}? (y/N) "
        try:
            self.stdscr.addstr(h - 1, 0, prompt, curses.A_BOLD)
            self.stdscr.clrtoeol()
            self.stdscr.refresh()
        except curses.error:
            return

        key = self.stdscr.getch()
        if key in (ord('y'), ord('Y')):
            try:
                if selected.is_dir:
                    shutil.rmtree(selected.path)
                else:
                    os.unlink(selected.path)
                self._rescan()
            except OSError as e:
                self._show_error(str(e))

    def _show_error(self, msg: str):
        """Show error message briefly."""
        h, w = self.stdscr.getmaxyx()
        display = f" Error: {msg} "[:w - 1]
        try:
            self.stdscr.addstr(
                h - 1, 0, display,
                curses.color_pair(4) | curses.A_BOLD
            )
            self.stdscr.clrtoeol()
            self.stdscr.refresh()
        except curses.error:
            pass
        time.sleep(1.5)

    def _rescan(self):
        """Rescan current directory."""
        if self.current_node:
            self._scan(self.current_node.path)
            self._apply_sort()
            self._clamp_cursor()

    def _draw(self):
        """Draw the full UI."""
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        if h < 5 or w < 40:
            try:
                self.stdscr.addstr(0, 0, "Terminal too small")
            except curses.error:
                pass
            self.stdscr.refresh()
            return

        if self.show_help:
            self._draw_help(h, w)
            self.stdscr.refresh()
            return

        self._draw_header(w)
        self._draw_content(h, w)
        self._draw_footer(h, w)
        self.stdscr.refresh()

    def _draw_header(self, w: int):
        """Draw header bar."""
        if not self.current_node:
            return
        path_display = self.current_node.path
        size_display = format_size(self.current_node.size)
        sort_label = self.SORT_LABELS[self.sort_mode_idx]

        left = f" diskvu: {path_display}"
        right = f"{size_display} total [{sort_label}] "
        padding = max(0, w - len(left) - len(right))
        header = (left + " " * padding + right)[:w - 1]

        try:
            self.stdscr.addstr(0, 0, header, curses.color_pair(5) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_content(self, h: int, w: int):
        """Draw file/directory listing."""
        if not self.current_node or not self.current_node.children:
            msg = "  (empty)"
            if self.current_node and self.current_node.error:
                msg = f"  Error: {self.current_node.error}"
            try:
                self.stdscr.addstr(2, 0, msg)
            except curses.error:
                pass
            return

        content_height = h - 4
        children = self.current_node.children
        max_size = max((c.size for c in children), default=1) or 1

        for i in range(self.scroll_offset, min(len(children), self.scroll_offset + content_height)):
            row = i - self.scroll_offset + 2
            child = children[i]
            is_selected = (i == self.cursor_pos)

            size_str = format_size(child.size).rjust(8)
            bar_width = 10
            bar_fill = int((child.size / max_size) * bar_width) if max_size > 0 else 0
            bar = "#" * bar_fill + " " * (bar_width - bar_fill)

            name = child.name
            if child.is_dir:
                name += "/"
            if child.error:
                name += " [!]"

            file_count_str = f"({child.file_count:,} file{'s' if child.file_count != 1 else ''})"

            line = f"  {size_str} [{bar}] {name}"
            right_part = f"  {file_count_str}"
            available = w - len(line) - len(right_part) - 1
            if available > 0:
                line = line + " " * available + right_part
            else:
                line = line[:w - 1]

            attr = curses.A_REVERSE if is_selected else 0
            if child.is_dir and not is_selected:
                attr |= curses.color_pair(1)
            if child.error and not is_selected:
                attr |= curses.color_pair(3)

            try:
                self.stdscr.addstr(row, 0, line[:w - 1], attr)
            except curses.error:
                pass

    def _draw_footer(self, h: int, w: int):
        """Draw footer with keybindings and selected path."""
        if not self.current_node:
            return

        status = ""
        if self.current_node.children and self.cursor_pos < len(self.current_node.children):
            selected = self.current_node.children[self.cursor_pos]
            status = f" {selected.path}"

        try:
            self.stdscr.addstr(h - 2, 0, status[:w - 1], curses.color_pair(2))
        except curses.error:
            pass

        hints = " [s]ort [d]elete [r]escan [?]help [q]uit"
        try:
            self.stdscr.addstr(h - 1, 0, hints[:w - 1], curses.A_DIM)
        except curses.error:
            pass

    def _draw_help(self, h: int, w: int):
        """Draw help overlay."""
        help_lines = [
            "diskvu — Keyboard Shortcuts",
            "",
            "  ↑ / k        Move cursor up",
            "  ↓ / j        Move cursor down",
            "  Enter / → / l  Enter directory",
            "  Backspace / ← / h  Go to parent",
            "  s            Cycle sort mode",
            "  d            Delete selected (with confirm)",
            "  r            Rescan current directory",
            "  ?            Toggle this help",
            "  q / Esc      Quit",
            "",
            "  Press any key to close this help.",
        ]

        start_y = max(0, (h - len(help_lines)) // 2)
        for i, line in enumerate(help_lines):
            y = start_y + i
            if y >= h:
                break
            x = max(0, (w - len(line)) // 2)
            try:
                attr = curses.A_BOLD if i == 0 else 0
                self.stdscr.addstr(y, x, line, attr)
            except curses.error:
                pass


def main():
    parser = argparse.ArgumentParser(
        prog="diskvu",
        description="Interactive terminal disk usage analyzer"
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Directory to analyze (default: current directory)"
    )
    args = parser.parse_args()

    target = os.path.abspath(args.path)
    if not os.path.isdir(target):
        print(f"Error: '{args.path}' is not a directory")
        raise SystemExit(1)

    app = DiskVuApp(target)
    try:
        curses.wrapper(app.run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
