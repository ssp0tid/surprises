"""System notification service."""

import logging

logger = logging.getLogger(__name__)


class Notifier:
    """System notification dispatcher."""

    def __init__(self) -> None:
        self._notify = None
        self._try_import()

    def _try_import(self) -> None:
        """Try to import notification library."""
        try:
            from notify_run import Notify
            self._notify = Notify()
        except ImportError:
            logger.warning("notify-run not available, notifications disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize notifications: {e}")

    async def notify(self, title: str, message: str) -> None:
        """Send a system notification."""
        try:
            if self._notify:
                self._notify.send(title=title, message=message)
                logger.info(f"Notification sent: {title}")
            else:
                logger.info(f"Notification (fallback): {title} - {message}")
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
            # Fallback: just log
            print(f"NOTIFICATION: {title} - {message}")

    async def notify_timer_complete(self) -> None:
        """Send timer completion notification."""
        await self.notify("Timer Complete!", "Your timer has finished.")

    async def notify_alarm(self, label: str, time_str: str) -> None:
        """Send alarm notification."""
        await self.notify(label, f"Alarm at {time_str}")

    async def notify_pomodoro_work_complete(self, session_count: int) -> None:
        """Send pomodoro work session complete notification."""
        await self.notify(
            "Work Session Complete!",
            f"Great job! You've completed {session_count} pomodoro(s)."
        )

    async def notify_pomodoro_break_complete(self) -> None:
        """Send pomodoro break complete notification."""
        await self.notify("Break Complete!", "Time to get back to work!")


class NotificationService:
    """Alias for Notifier for backwards compatibility."""

    def __init__(self) -> None:
        self.notifier = Notifier()

    async def notify(self, title: str, message: str) -> None:
        """Send notification."""
        await self.notifier.notify(title, message)