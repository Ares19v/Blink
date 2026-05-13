"""
notifier.py  v2
OS toast + configurable beep count.
  beep_count=1  → blink reminder
  beep_count=2  → 20-20-20 break reminder
"""
import threading
import time

from core.logger_setup import logger


def notify(
    title: str = "Blink! 👁️",
    message: str = "Hey! Don't forget to blink.",
    beep_count: int = 1,
) -> None:
    """Fire-and-forget in a daemon thread."""
    t = threading.Thread(target=_worker, args=(title, message, beep_count), daemon=True)
    t.start()


def _worker(title: str, message: str, beep_count: int) -> None:
    # OS Toast
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="Blink", timeout=5)
    except Exception as exc:
        logger.warning(f"Toast notification failed: {exc}")

    # Beeps
    _beep(beep_count)


def _beep(count: int) -> None:
    try:
        import winsound
        for i in range(count):
            winsound.Beep(880, 250)
            if i < count - 1:
                time.sleep(0.15)
    except ImportError:
        import os
        for _ in range(count):
            os.system("printf '\\a'")
            time.sleep(0.15)
    except Exception as exc:
        logger.warning(f"Beep failed: {exc}")
