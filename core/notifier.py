"""
notifier.py
Sends an OS-level toast notification and plays a single short beep.
Runs in a daemon thread so it never blocks the main loop.
"""
import threading


def notify(
    title: str = "Blink! 👁️",
    message: str = "Hey! Don't forget to blink.",
):
    """Fire-and-forget: toast + beep in background thread."""
    t = threading.Thread(target=_notify_worker, args=(title, message), daemon=True)
    t.start()


def _notify_worker(title: str, message: str):
    # --- OS Toast ---
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Blink",
            timeout=5,
        )
    except Exception as exc:
        print(f"[notifier] toast failed: {exc}")

    # --- Beep (Windows: winsound; other OS: terminal bell) ---
    try:
        import winsound
        winsound.Beep(880, 250)   # 880 Hz, 250 ms — short, not annoying
    except ImportError:
        # Linux / macOS fallback
        import os
        os.system("printf '\\a'")
    except Exception as exc:
        print(f"[notifier] beep failed: {exc}")
