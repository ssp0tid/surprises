#!/usr/bin/env python3
"""
Usage:
  maze.py play [--size WxH] [--algo recursive|kruskals|prims] [--seed INT]
  maze.py solve [--size WxH] [--algo recursive|kruskals|prims] [--solver bfs|dfs|astar] [--speed FLOAT] [--seed INT]
  maze.py generate [--size WxH] [--algo recursive|kruskals|prims] [--no-render] [--seed INT]
  maze.py --help
"""

import argparse
import curses
import json
import os
from datetime import date

from generator import ALGORITHMS
from solver import SOLVERS
from renderer import MazeRenderer, COLOR_PATH, COLOR_MARKER
from player import PlayerMode

HIGHSCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")


def parse_size(size_str):
    try:
        parts = size_str.lower().split("x")
        if len(parts) != 2:
            raise ValueError
        w, h = int(parts[0]), int(parts[1])
        if w < 2 or h < 2:
            raise argparse.ArgumentTypeError(f"Minimum size is 2x2, got '{size_str}'")
        if w > 200 or h > 200:
            raise argparse.ArgumentTypeError(f"Maximum size is 200x200, got '{size_str}'")
        return w, h
    except (ValueError, IndexError):
        raise argparse.ArgumentTypeError(f"Invalid size '{size_str}'. Use WxH format (e.g. 20x10)")


def load_highscores():
    if not os.path.exists(HIGHSCORES_FILE):
        return []
    try:
        with open(HIGHSCORES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_highscore(size_str, algo, elapsed, moves):
    scores = load_highscores()
    scores.append({
        "size": size_str,
        "algo": algo,
        "time": round(elapsed, 1),
        "moves": moves,
        "date": date.today().isoformat(),
    })

    key_scores = [s for s in scores if s["size"] == size_str and s["algo"] == algo]
    key_scores.sort(key=lambda s: s["time"])
    top_10 = key_scores[:10]

    other_scores = [s for s in scores if not (s["size"] == size_str and s["algo"] == algo)]
    scores = other_scores + top_10

    try:
        with open(HIGHSCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except IOError:
        pass


def show_highscores(stdscr, size_str, algo):
    scores = load_highscores()
    key_scores = [s for s in scores if s["size"] == size_str and s["algo"] == algo]
    key_scores.sort(key=lambda s: s["time"])

    if not key_scores:
        return

    max_y, max_x = stdscr.getmaxyx()
    start_y = 2
    stdscr.addnstr(start_y, 0, f"High Scores ({size_str}, {algo}):", max_x - 1)
    for i, score in enumerate(key_scores[:10]):
        if start_y + 1 + i >= max_y - 1:
            break
        line = f"  {i+1:2d}. {score['time']:6.1f}s  {score['moves']:4d} moves  ({score['date']})"
        stdscr.addnstr(start_y + 1 + i, 0, line, max_x - 1)
    stdscr.refresh()


def run_play(stdscr, width, height, algo, seed):
    generate = ALGORITHMS[algo]
    maze = generate(width, height, seed)

    player_mode = PlayerMode(stdscr, maze, width, height)
    elapsed = player_mode.run()

    if elapsed is not None:
        size_str = f"{width}x{height}"
        save_highscore(size_str, algo, elapsed, player_mode.moves)
        stdscr.clear()
        stdscr.addstr(0, 0, f"Completed in {elapsed:.1f}s with {player_mode.moves} moves!")
        show_highscores(stdscr, size_str, algo)
        max_y, _ = stdscr.getmaxyx()
        stdscr.addnstr(max_y - 1, 0, "Press any key to exit.", curses.COLS - 1)
        stdscr.refresh()
        stdscr.nodelay(False)
        stdscr.getch()


def run_solve(stdscr, width, height, algo, solver_name, speed, seed):
    generate = ALGORITHMS[algo]
    maze = generate(width, height, seed)

    renderer = MazeRenderer(stdscr, maze)
    if not renderer.check_terminal_size():
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal too small! Resize and try again.")
        stdscr.addstr(1, 0, f"Need: {renderer.screen_cols}x{renderer.screen_rows + 2}")
        stdscr.addstr(2, 0, "Press any key to exit.")
        stdscr.getch()
        return

    renderer.draw_maze()
    renderer.highlight_cell(0, 0, COLOR_MARKER)
    renderer.highlight_cell(height - 1, width - 1, COLOR_MARKER)
    renderer.draw_status(f"Solving with {solver_name}... Press Q to skip")
    renderer.stdscr.refresh()

    solve_fn = SOLVERS[solver_name]
    solver_gen = solve_fn(maze, (0, 0), (height - 1, width - 1))
    final_path = renderer.animate_solve(solver_gen, speed)

    renderer.draw_maze()
    if final_path:
        renderer.draw_path(final_path, COLOR_PATH)
    renderer.highlight_cell(0, 0, COLOR_MARKER)
    renderer.highlight_cell(height - 1, width - 1, COLOR_MARKER)
    renderer.draw_status(
        f"Done! Path length: {len(final_path) if final_path else 'No path'} | Press any key to exit"
    )
    stdscr.nodelay(False)
    stdscr.getch()


def run_generate(stdscr, width, height, algo, seed):
    generate = ALGORITHMS[algo]
    maze = generate(width, height, seed)

    renderer = MazeRenderer(stdscr, maze)
    if not renderer.check_terminal_size():
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal too small! Resize and try again.")
        stdscr.addstr(1, 0, f"Need: {renderer.screen_cols}x{renderer.screen_rows + 2}")
        stdscr.addstr(2, 0, "Press any key to exit.")
        stdscr.getch()
        return

    renderer.draw_maze()
    renderer.highlight_cell(0, 0, COLOR_MARKER)
    renderer.highlight_cell(height - 1, width - 1, COLOR_MARKER)
    renderer.draw_status(f"Maze ({width}x{height}, {algo}) | Press any key to exit")
    stdscr.getch()


def run_generate_no_render(width, height, algo, seed):
    generate = ALGORITHMS[algo]
    maze = generate(width, height, seed)

    N, E, S, W = 1, 2, 4, 8
    lines = []

    for row in range(height):
        top_line = ""
        mid_line = ""
        for col in range(width):
            cell = maze[row][col]
            has_n = bool(cell & N)
            has_w = bool(cell & W)
            top_line += "+" + ("---" if has_n else "   ")
            mid_line += ("|" if has_w else " ") + "   "

        has_e = bool(maze[row][width - 1] & E)
        top_line += "+"
        mid_line += "|" if has_e else " "
        lines.append(top_line)
        lines.append(mid_line)

    bottom = ""
    for col in range(width):
        has_s = bool(maze[height - 1][col] & S)
        bottom += "+" + ("---" if has_s else "   ")
    bottom += "+"
    lines.append(bottom)

    print("\n".join(lines))
    print(f"\nMaze: {width}x{height}, algorithm: {algo}" + (f", seed: {seed}" if seed else ""))


def main():
    parser = argparse.ArgumentParser(
        description="Terminal maze game with generation, solving, and playable mode.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="mode")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--size", type=parse_size, default="20x10",
                        help="Maze size as WxH (default: 20x10)")
    common.add_argument("--algo", choices=["recursive", "kruskals", "prims"],
                        default="recursive", help="Generation algorithm (default: recursive)")
    common.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible mazes")

    subparsers.add_parser("play", parents=[common],
                          help="Play the maze interactively")

    solve_parser = subparsers.add_parser("solve", parents=[common],
                                         help="Watch the maze being solved")
    solve_parser.add_argument("--solver", choices=["bfs", "dfs", "astar"],
                              default="bfs", help="Solving algorithm (default: bfs)")
    solve_parser.add_argument("--speed", type=float, default=0.05,
                              help="Animation speed in seconds per step (default: 0.05)")

    gen_parser = subparsers.add_parser("generate", parents=[common],
                                       help="Generate and display a maze")
    gen_parser.add_argument("--no-render", action="store_true",
                            help="Print maze to stdout without curses")

    args = parser.parse_args()

    if args.mode is None:
        args.mode = "play"
        args.size = (20, 10)
        args.algo = "recursive"
        args.seed = None

    width, height = args.size if isinstance(args.size, tuple) else parse_size(args.size)

    if args.mode == "generate" and getattr(args, "no_render", False):
        run_generate_no_render(width, height, args.algo, args.seed)
        return

    def curses_main(stdscr):
        curses.curs_set(0)
        if args.mode == "play":
            run_play(stdscr, width, height, args.algo, args.seed)
        elif args.mode == "solve":
            run_solve(stdscr, width, height, args.algo, args.solver, args.speed, args.seed)
        elif args.mode == "generate":
            run_generate(stdscr, width, height, args.algo, args.seed)

    try:
        curses.wrapper(curses_main)
    except KeyboardInterrupt:
        pass
    except curses.error as e:
        print(f"Error: Could not initialize terminal display: {e}")
        print("Make sure you're running in a terminal that supports curses.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
