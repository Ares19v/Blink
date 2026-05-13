"""
main.py — Blink entry point.

Usage:
    python main.py
"""
import sys
import os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from gui.app import MainWindow


def main():
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
