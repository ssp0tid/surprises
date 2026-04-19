"""High score persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import textual.logging

logger = textual.logging.get_logger()


class HighScoreManager:
    """Manages high score persistence using JSON file."""

    def __init__(self, filepath: Optional[Path] = None) -> None:
        if filepath is None:
            self._filepath = Path(__file__).parent.parent.parent / "assets" / "high_scores.json"
        else:
            self._filepath = Path(filepath)

        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._scores: list[tuple[str, int]] = []
        self._load_scores()

    def _load_scores(self) -> None:
        """Load scores from JSON file."""
        if not self._filepath.exists():
            self._scores = []
            return

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                self._scores = []
                for entry in data:
                    if isinstance(entry, list) and len(entry) == 2:
                        name, score = entry
                        if isinstance(name, str) and isinstance(score, int):
                            self._scores.append((name, score))
                    elif isinstance(entry, dict) and "name" in entry and "score" in entry:
                        self._scores.append((str(entry["name"]), int(entry["score"])))

            self._scores.sort(key=lambda x: x[1], reverse=True)
            logger.info(f"Loaded {len(self._scores)} high scores")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load high scores: {e}")
            self._scores = []

    def _save_scores(self) -> None:
        """Save scores to JSON file using atomic write."""
        try:
            temp_path = self._filepath.with_suffix(".tmp")

            data = [[name, score] for name, score in self._scores[:10]]

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            temp_path.replace(self._filepath)
            logger.info("High scores saved successfully")
        except IOError as e:
            logger.error(f"Failed to save high scores: {e}")

    def get_scores(self) -> list[tuple[str, int]]:
        """Get all high scores sorted by score descending."""
        return self._scores.copy()

    def add_score(self, name: str, score: int) -> int:
        """Add a new high score. Returns the rank (1-indexed) or -1 if not a high score."""
        entry = (name[:20], score)

        if self._scores and score < self._scores[-1][1] and len(self._scores) >= 10:
            return -1

        self._scores.append(entry)
        self._scores.sort(key=lambda x: x[1], reverse=True)

        if len(self._scores) > 10:
            self._scores = self._scores[:10]

        self._save_scores()

        for i, (n, s) in enumerate(self._scores):
            if n == name and s == score:
                return i + 1

        return -1

    def is_high_score(self, score: int) -> bool:
        """Check if a score would qualify as a high score."""
        if len(self._scores) < 10:
            return True
        return score > self._scores[-1][1]

    def clear_scores(self) -> None:
        """Clear all high scores."""
        self._scores = []
        self._save_scores()
