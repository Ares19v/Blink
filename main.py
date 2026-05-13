"""
main.py — Blink entry point.

Usage:
    python main.py
"""

import sys
import os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication  # noqa: E402
from gui.app import MainWindow  # noqa: E402


def exception_hook(exc_type, exc_value, exc_traceback):
    import traceback

    print("UNCAUGHT EXCEPTION:", exc_type, exc_value)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    sys.exit(1)


def main():
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    app.setApplicationName("Blink")
    app.setApplicationDisplayName("Blink — Eye Health Monitor")

    # Keep the app alive even when the main window is hidden to tray
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
