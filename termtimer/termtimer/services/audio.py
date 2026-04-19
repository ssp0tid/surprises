"""Audio playback service."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Sound playback service for alarms."""

    def __init__(self) -> None:
        self._playsound = None
        self._default_sound = self._get_default_sound_path()
        self._try_import()

    def _try_import(self) -> None:
        """Try to import playsound library."""
        try:
            from playsound import playsound
            self._playsound = playsound
        except ImportError:
            logger.warning("playsound not available, audio disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize audio: {e}")

    def _get_default_sound_path(self) -> str:
        """Get path to default alarm sound."""
        # Check in termtimer/sounds/ directory
        module_dir = Path(__file__).parent.parent
        sound_path = module_dir / "sounds" / "alarm.mp3"
        if sound_path.exists():
            return str(sound_path)
        return ""

    async def play_alarm(self, sound_path: str = "") -> None:
        """Play alarm sound."""
        path = sound_path or self._default_sound

        try:
            if self._playsound and path and os.path.exists(path):
                # playsound is blocking, run in executor
                import asyncio
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._playsound, path)
                logger.info(f"Played alarm sound: {path}")
            else:
                # Fallback: just print
                print("🔔 ALARM! 🔔")
        except Exception as e:
            logger.warning(f"Failed to play alarm sound: {e}")
            print("🔔 ALARM! 🔔")

    async def play_completion(self) -> None:
        """Play completion sound (same as alarm for now)."""
        await self.play_alarm()


class AudioService:
    """Alias for AudioPlayer for backwards compatibility."""

    def __init__(self) -> None:
        self.player = AudioPlayer()

    async def play_alarm(self, sound_path: str = "") -> None:
        """Play alarm."""
        await self.player.play_alarm(sound_path)