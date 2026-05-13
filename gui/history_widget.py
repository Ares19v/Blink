"""
history_widget.py
Standalone window showing session history charts (matplotlib in PyQt6).
"""
from datetime import datetime

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from core.database import get_sessions
from core.logger_setup import logger

_BG = "#0a0a0a"
_CYAN = "#00f5ff"
_MUTED = "#444444"
_TEXT = "#e0e0e0"


class HistoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Blink — Session History")
        self.setMinimumSize(820, 500)
        self.setStyleSheet(f"background:{_BG}; color:{_TEXT}; font-family:'Segoe UI';")
        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Session History")
        title.setStyleSheet(f"color:{_CYAN}; font-size:18px; font-weight:700;")
        hdr.addWidget(title)
        hdr.addStretch()

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setStyleSheet(
            f"background:#111; color:{_CYAN}; border:1px solid {_CYAN};"
            "border-radius:5px; padding:6px 14px; font-weight:600;"
        )
        refresh_btn.clicked.connect(self._load_data)
        hdr.addWidget(refresh_btn)
        lay.addLayout(hdr)

        self._no_data_lbl = QLabel("No sessions recorded yet.")
        self._no_data_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_data_lbl.setStyleSheet(f"color:{_MUTED}; font-size:14px;")
        self._no_data_lbl.hide()
        lay.addWidget(self._no_data_lbl)

        # Matplotlib figure
        self._fig, self._axes = plt.subplots(1, 2, figsize=(12, 4))
        self._fig.patch.set_facecolor(_BG)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setStyleSheet(f"background:{_BG};")
        lay.addWidget(self._canvas)

    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        rows = get_sessions(limit=10)
        if not rows:
            self._no_data_lbl.show()
            self._canvas.hide()
            logger.info("History: no sessions found")
            return

        self._no_data_lbl.hide()
        self._canvas.show()
        self._draw(rows)

    def _draw(self, rows: list[tuple]) -> None:
        # rows: (start_time, end_time, duration_secs, total_blinks, avg_blink_rate, avg_fatigue_score, avg_blink_duration_ms)
        labels   = []
        rates    = []
        fatigues = []

        for row in reversed(rows):
            start_str = row[0]
            try:
                dt = datetime.fromisoformat(start_str)
                label = dt.strftime("%d %b\n%H:%M")
            except Exception:
                label = start_str[:10]
            labels.append(label)
            rates.append(row[4] if row[4] else 0)
            fatigues.append(row[5] if row[5] else 0)

        ax1, ax2 = self._axes
        ax1.clear()
        ax2.clear()

        # Chart 1: Blink Rate
        bars1 = ax1.bar(range(len(labels)), rates, color=_CYAN, alpha=0.85, width=0.6)
        ax1.axhline(12, color="#ff5555", linestyle="--", linewidth=1, label="Min healthy (12/min)")
        ax1.set_xticks(range(len(labels)))
        ax1.set_xticklabels(labels, color=_TEXT, fontsize=8)
        ax1.set_ylabel("Blinks / min", color=_TEXT)
        ax1.set_title("Avg Blink Rate per Session", color=_CYAN, fontsize=11, pad=10)
        ax1.set_facecolor(_BG)
        ax1.tick_params(colors=_TEXT)
        ax1.spines[:].set_color(_MUTED)
        ax1.legend(facecolor="#111", edgecolor=_MUTED, labelcolor=_TEXT, fontsize=8)

        # Chart 2: Fatigue Score
        fatigue_colors = [
            "#00f5ff" if f < 40 else "#ffaa00" if f < 70 else "#ff5555"
            for f in fatigues
        ]
        ax2.bar(range(len(labels)), fatigues, color=fatigue_colors, alpha=0.85, width=0.6)
        ax2.axhline(40, color="#ffaa00", linestyle="--", linewidth=1, label="Moderate (40)")
        ax2.axhline(70, color="#ff5555", linestyle="--", linewidth=1, label="High (70)")
        ax2.set_xticks(range(len(labels)))
        ax2.set_xticklabels(labels, color=_TEXT, fontsize=8)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("Fatigue Score (0–100)", color=_TEXT)
        ax2.set_title("Avg Fatigue Score per Session", color=_CYAN, fontsize=11, pad=10)
        ax2.set_facecolor(_BG)
        ax2.tick_params(colors=_TEXT)
        ax2.spines[:].set_color(_MUTED)
        ax2.legend(facecolor="#111", edgecolor=_MUTED, labelcolor=_TEXT, fontsize=8)

        self._fig.tight_layout(pad=2.0)
        self._canvas.draw()
        logger.info(f"History chart drawn with {len(rows)} sessions")
