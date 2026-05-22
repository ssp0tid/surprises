#!/usr/bin/env python3
import argparse
import curses
import random
import time
from datetime import date

from words import EASY_WORDS, MEDIUM_WORDS, HARD_WORDS
from texts import CODE_SNIPPETS, PARAGRAPHS
from stats import calculate_wpm, calculate_accuracy, save_score, load_scores

TITLE_ART = [
    " _____ __   __ ____  ___  _   _  ____   ____   ___      _  ___  ",
    "|_   _|\\ \\ / /|  _ \\|_ _|| \\ | |/ ___| |  _ \\ / _ \\    | |/ _ \\ ",
    "  | |   \\ V / | |_) || | |  \\| | |  _  | | | | | | |_  | | | | |",
    "  | |    | |  |  __/ | | | |\\  | |_| | | |_| | |_| | |_| | |_| |",
    "  |_|    |_|  |_|   |___||_| \\_|\\____| |____/ \\___/ \\___/ \\___/ ",
]


def get_words_for_difficulty(difficulty: str) -> list[str]:
    if difficulty == "easy":
        return EASY_WORDS
    elif difficulty == "medium":
        return MEDIUM_WORDS
    elif difficulty == "hard":
        return HARD_WORDS
    return MEDIUM_WORDS


def draw_header(stdscr, mode_label: str = "", wpm: float = 0, time_left: str = ""):
    h, w = stdscr.getmaxyx()
    header = " TYPING DOJO"
    right = ""
    if wpm > 0:
        right += f"WPM: {wpm:.0f}  "
    if time_left:
        right += f"Time: {time_left}"
    padding = w - len(header) - len(right) - 2
    if padding < 0:
        padding = 0
    line = header + " " * padding + right
    stdscr.attron(curses.color_pair(4))
    stdscr.addstr(0, 0, line[:w - 1].ljust(w - 1))
    stdscr.attroff(curses.color_pair(4))


def draw_footer(stdscr, accuracy: float, words_done: int, total_words: int, errors: int):
    h, w = stdscr.getmaxyx()
    footer = f"  Accuracy: {accuracy:.1f}%  |  Words: {words_done}/{total_words}  |  Errors: {errors}"
    stdscr.attron(curses.color_pair(4))
    stdscr.addstr(h - 1, 0, footer[:w - 1].ljust(w - 1))
    stdscr.attroff(curses.color_pair(4))


def show_results(stdscr, wpm: float, accuracy: float, time_taken: float, correct: int, incorrect: int):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    results = [
        "=== RESULTS ===",
        "",
        f"  WPM:        {wpm:.1f}",
        f"  Accuracy:   {accuracy:.1f}%",
        f"  Time:       {time_taken:.1f}s",
        f"  Correct:    {correct}",
        f"  Incorrect:  {incorrect}",
        "",
        "  Press any key to continue...",
    ]
    start_y = max(0, (h - len(results)) // 2)
    for i, line in enumerate(results):
        y = start_y + i
        if y >= h:
            break
        x = max(0, (w - len(line)) // 2)
        stdscr.addstr(y, x, line[:w - 1])
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def typing_test(stdscr, prompt_text: str, timed: bool = False, duration: int = 0):
    curses.curs_set(0)
    stdscr.nodelay(timed)
    stdscr.clear()

    h, w = stdscr.getmaxyx()
    usable_w = w - 4
    typed_chars: list[str] = []
    correct_count = 0
    incorrect_count = 0
    start_time = None
    finished = False

    while not finished:
        stdscr.clear()

        elapsed = 0.0
        current_wpm = 0.0
        if start_time:
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_wpm = calculate_wpm(len(typed_chars), elapsed)

        time_str = ""
        if timed and duration > 0:
            remaining = max(0, duration - elapsed)
            time_str = f"{remaining:.0f}s"
            if remaining <= 0:
                finished = True
                break

        draw_header(stdscr, wpm=current_wpm, time_left=time_str)

        total_typed = len(typed_chars)
        total_accuracy = calculate_accuracy(correct_count, correct_count + incorrect_count)
        words_done = typed_chars.count(" ") if typed_chars else 0
        total_words = prompt_text.count(" ") + 1
        draw_footer(stdscr, total_accuracy, words_done, total_words, incorrect_count)

        display_y = max(2, (h - 4) // 2)
        col = 2
        for i, ch in enumerate(prompt_text):
            if display_y >= h - 1:
                break
            if col >= w - 2:
                display_y += 1
                col = 2
                if display_y >= h - 1:
                    break

            if i < total_typed:
                if typed_chars[i] == ch:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(display_y, col, ch)
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(display_y, col, ch)
                    stdscr.attroff(curses.color_pair(2))
            elif i == total_typed:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(display_y, col, ch)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(display_y, col, ch)
            col += 1

        stdscr.refresh()

        try:
            key = stdscr.getch()
        except curses.error:
            continue

        if key == -1:
            continue

        if start_time is None and key not in (curses.KEY_RESIZE, 27):
            start_time = time.time()

        if key == 27:
            return None
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if typed_chars:
                removed = typed_chars.pop()
                idx = len(typed_chars)
                if idx < len(prompt_text):
                    if removed == prompt_text[idx]:
                        correct_count -= 1
                    else:
                        incorrect_count -= 1
        elif key == curses.KEY_RESIZE:
            continue
        elif 32 <= key <= 126:
            ch = chr(key)
            idx = len(typed_chars)
            if idx < len(prompt_text):
                typed_chars.append(ch)
                if ch == prompt_text[idx]:
                    correct_count += 1
                else:
                    incorrect_count += 1

            if len(typed_chars) >= len(prompt_text):
                finished = True

    if start_time is None:
        return None

    elapsed = time.time() - start_time
    total_chars = correct_count + incorrect_count
    wpm = calculate_wpm(total_chars, elapsed)
    accuracy = calculate_accuracy(correct_count, total_chars)

    return {
        "wpm": round(wpm, 1),
        "accuracy": round(accuracy, 1),
        "time": round(elapsed, 1),
        "correct": correct_count,
        "incorrect": incorrect_count,
    }


def quick_test(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    options = ["Easy", "Medium", "Hard"]
    selected = 0

    while True:
        stdscr.clear()
        title = "Select Difficulty"
        stdscr.addstr(h // 2 - 3, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
        for i, opt in enumerate(options):
            y = h // 2 - 1 + i
            x = max(0, (w - len(opt) - 4) // 2)
            if i == selected:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, f"> {opt} <")
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(y, x, f"  {opt}  ")
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(options) - 1:
            selected += 1
        elif key in (10, 13, curses.KEY_ENTER):
            break
        elif key == 27:
            return

    difficulty = options[selected].lower()
    word_list = get_words_for_difficulty(difficulty)
    num_words = random.randint(10, 20)
    words = random.sample(word_list, min(num_words, len(word_list)))
    prompt_text = " ".join(words)

    result = typing_test(stdscr, prompt_text)
    if result:
        result["difficulty"] = difficulty
        result["date"] = str(date.today())
        save_score("quick", result)
        show_results(stdscr, result["wpm"], result["accuracy"], result["time"],
                     result["correct"], result["incorrect"])


def timed_test(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    durations = [15, 30, 60, 120]
    options = [f"{d}s" for d in durations]
    selected = 0

    while True:
        stdscr.clear()
        title = "Select Duration"
        stdscr.addstr(h // 2 - 3, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
        for i, opt in enumerate(options):
            y = h // 2 - 1 + i
            x = max(0, (w - len(opt) - 4) // 2)
            if i == selected:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, f"> {opt} <")
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(y, x, f"  {opt}  ")
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(options) - 1:
            selected += 1
        elif key in (10, 13, curses.KEY_ENTER):
            break
        elif key == 27:
            return

    duration = durations[selected]
    word_list = MEDIUM_WORDS
    words = []
    for _ in range(duration * 2):
        words.append(random.choice(word_list))
    prompt_text = " ".join(words)

    result = typing_test(stdscr, prompt_text, timed=True, duration=duration)
    if result:
        result["duration"] = duration
        result["date"] = str(date.today())
        save_score("timed", result)
        show_results(stdscr, result["wpm"], result["accuracy"], result["time"],
                     result["correct"], result["incorrect"])


def code_mode(stdscr):
    snippet = random.choice(CODE_SNIPPETS)
    result = typing_test(stdscr, snippet)
    if result:
        result["date"] = str(date.today())
        save_score("code", result)
        show_results(stdscr, result["wpm"], result["accuracy"], result["time"],
                     result["correct"], result["incorrect"])


def high_scores(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    scores = load_scores()

    lines = ["=== HIGH SCORES ===", ""]
    for mode in ("quick", "timed", "code"):
        lines.append(f"  [{mode.upper()}]")
        mode_scores = scores.get(mode, [])
        if not mode_scores:
            lines.append("    No scores yet.")
        else:
            for i, s in enumerate(mode_scores[:10], 1):
                wpm = s.get("wpm", 0)
                acc = s.get("accuracy", 0)
                d = s.get("date", "?")
                lines.append(f"    {i:>2}. {wpm:>5.1f} WPM  {acc:>5.1f}%  {d}")
        lines.append("")

    lines.append("  Press any key to return...")

    start_y = max(0, (h - len(lines)) // 2)
    for i, line in enumerate(lines):
        y = start_y + i
        if y >= h:
            break
        x = max(0, (w - len(line)) // 2) if i == 0 else 2
        stdscr.addstr(y, x, line[:w - 1])

    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def main_menu(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.curs_set(0)

    menu_items = [
        "[1] Quick Test",
        "[2] Timed Test",
        "[3] Code Mode",
        "[4] High Scores",
        "[5] Quit",
    ]
    selected = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        title_start_y = max(1, h // 2 - len(TITLE_ART) - 4)
        for i, line in enumerate(TITLE_ART):
            y = title_start_y + i
            x = max(0, (w - len(line)) // 2)
            if y < h:
                stdscr.addstr(y, x, line[:w - 1], curses.A_BOLD)

        menu_start_y = title_start_y + len(TITLE_ART) + 2
        for i, item in enumerate(menu_items):
            y = menu_start_y + i
            if y >= h - 1:
                break
            x = max(0, (w - len(item) - 4) // 2)
            if i == selected:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, f"> {item} <")
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(y, x, f"  {item}  ")

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(menu_items) - 1:
            selected += 1
        elif key in (10, 13, curses.KEY_ENTER):
            if selected == 0:
                quick_test(stdscr)
            elif selected == 1:
                timed_test(stdscr)
            elif selected == 2:
                code_mode(stdscr)
            elif selected == 3:
                high_scores(stdscr)
            elif selected == 4:
                break
        elif key == ord("1"):
            quick_test(stdscr)
        elif key == ord("2"):
            timed_test(stdscr)
        elif key == ord("3"):
            code_mode(stdscr)
        elif key == ord("4"):
            high_scores(stdscr)
        elif key == ord("5") or key == ord("q") or key == 27:
            break


def main():
    parser = argparse.ArgumentParser(
        description="Typing Dojo - Terminal typing speed trainer"
    )
    parser.add_argument("--quick", action="store_true", help="Jump to quick test")
    parser.add_argument("--timed", type=int, metavar="SECONDS",
                        help="Jump to timed test (15, 30, 60, or 120 seconds)")
    args = parser.parse_args()

    if args.quick:
        curses.wrapper(quick_test)
    elif args.timed:
        if args.timed not in (15, 30, 60, 120):
            print("Error: --timed must be 15, 30, 60, or 120")
            raise SystemExit(1)

        def run_timed(stdscr):
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.curs_set(0)
            word_list = MEDIUM_WORDS
            words = [random.choice(word_list) for _ in range(args.timed * 2)]
            prompt_text = " ".join(words)
            result = typing_test(stdscr, prompt_text, timed=True, duration=args.timed)
            if result:
                result["duration"] = args.timed
                result["date"] = str(date.today())
                save_score("timed", result)
                show_results(stdscr, result["wpm"], result["accuracy"],
                             result["time"], result["correct"], result["incorrect"])

        curses.wrapper(run_timed)
    else:
        curses.wrapper(main_menu)


if __name__ == "__main__":
    main()
