import json
import time
from pathlib import Path

DATA_DIR = Path.home() / ".typing-dojo"
SCORES_FILE = DATA_DIR / "scores.json"


def calculate_wpm(chars_typed: int, seconds_elapsed: float) -> float:
    if seconds_elapsed <= 0:
        return 0.0
    return (chars_typed / 5) / (seconds_elapsed / 60)


def calculate_accuracy(correct_chars: int, total_chars: int) -> float:
    if total_chars <= 0:
        return 0.0
    return (correct_chars / total_chars) * 100


def load_scores() -> dict:
    if not SCORES_FILE.exists():
        return {"quick": [], "timed": [], "code": []}
    try:
        with open(SCORES_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"quick": [], "timed": [], "code": []}
    for mode in ("quick", "timed", "code"):
        if mode not in data:
            data[mode] = []
    return data


def save_score(mode: str, score: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    scores = load_scores()
    if mode not in scores:
        scores[mode] = []
    scores[mode].append(score)
    scores[mode].sort(key=lambda s: s.get("wpm", 0), reverse=True)
    scores[mode] = scores[mode][:10]
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except OSError:
        pass
