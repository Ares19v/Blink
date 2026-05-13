"""
app.py
PyQt6 main window for Blink.
- Left panel: live camera feed with landmarks
- Right panel: blink rate, EAR, session stats
- System tray: runs in background when window is closed
"""
import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSystemTrayIcon, QMenu,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QAction

from core.camera import CameraThread
from core.detector import BlinkDetector
from core.blink_monitor import BlinkMonitor
import core.notifier as notifier


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blink — Eye Health Monitor")
        self.setMinimumSize(980, 580)

        self._detector = BlinkDetector()
        self._monitor = BlinkMonitor()
        self._camera_thread: CameraThread | None = None
        self._is_monitoring = False

        self._build_ui()
        self._build_tray()
        self._load_stylesheet()

        # Refresh stats panel every second
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(1000)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        layout.addWidget(self._build_camera_panel(), stretch=3)
        layout.addWidget(self._build_stats_panel(), stretch=1)

    # ---- Left: camera ----

    def _build_camera_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("cameraPanel")
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        self._camera_lbl = QLabel("Camera feed will appear here\nonce monitoring starts.")
        self._camera_lbl.setObjectName("cameraLabel")
        self._camera_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._camera_lbl.setMinimumSize(640, 450)
        vbox.addWidget(self._camera_lbl)

        self._status_lbl = QLabel("● Not monitoring")
        self._status_lbl.setObjectName("statusLabel")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self._status_lbl)

        return panel

    # ---- Right: stats ----

    def _build_stats_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("statsPanel")
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(12)

        # Title
        title = QLabel("BLINK")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)

        sub = QLabel("Eye Health Monitor")
        sub.setObjectName("appSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(sub)

        vbox.addSpacing(12)

        # Big blink rate number
        self._rate_lbl = QLabel("--")
        self._rate_lbl.setObjectName("blinkRateBig")
        self._rate_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self._rate_lbl)

        unit = QLabel("blinks / min")
        unit.setObjectName("statUnit")
        unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(unit)

        vbox.addSpacing(8)

        # Stat cards
        self._ear_val,   ear_card   = self._stat_card("EAR Value",     "--")
        self._total_val, total_card = self._stat_card("Total Blinks",  "0")
        self._time_val,  time_card  = self._stat_card("Session Time",  "00:00")
        self._face_val,  face_card  = self._stat_card("Face",          "Not detected")

        for card in (ear_card, total_card, time_card, face_card):
            vbox.addWidget(card)

        vbox.addStretch()

        # Toggle button
        self._toggle_btn = QPushButton("▶  Start Monitoring")
        self._toggle_btn.setObjectName("toggleBtn")
        self._toggle_btn.clicked.connect(self._on_toggle)
        vbox.addWidget(self._toggle_btn)

        return panel

    @staticmethod
    def _stat_card(label_text: str, initial: str):
        """Returns (value_QLabel, card_QFrame)."""
        card = QFrame()
        card.setObjectName("statCard")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(12, 8, 12, 8)
        vbox.setSpacing(2)

        lbl = QLabel(label_text.upper())
        lbl.setObjectName("statLabel")
        vbox.addWidget(lbl)

        val = QLabel(initial)
        val.setObjectName("statValue")
        vbox.addWidget(val)

        return val, card

    # ------------------------------------------------------------------
    # Stylesheet
    # ------------------------------------------------------------------

    def _load_stylesheet(self):
        import os
        qss_path = os.path.join(os.path.dirname(__file__), "theme.qss")
        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("[app] theme.qss not found — running without stylesheet")

    # ------------------------------------------------------------------
    # System Tray
    # ------------------------------------------------------------------

    def _build_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        )
        self._tray.setToolTip("Blink — Eye Health Monitor")

        menu = QMenu()
        show_act = QAction("Show / Hide", self)
        show_act.triggered.connect(self._toggle_window)

        quit_act = QAction("Quit Blink", self)
        quit_act.triggered.connect(self._quit)

        menu.addAction(show_act)
        menu.addSeparator()
        menu.addAction(quit_act)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    # ------------------------------------------------------------------
    # Monitoring control
    # ------------------------------------------------------------------

    def _on_toggle(self):
        if not self._is_monitoring:
            self._start()
        else:
            self._stop()

    def _start(self):
        self._monitor.reset()
        self._camera_thread = CameraThread(self._detector)
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.error_occurred.connect(self._on_error)
        self._camera_thread.start()

        self._is_monitoring = True
        self._toggle_btn.setText("■  Stop Monitoring")
        self._toggle_btn.setObjectName("toggleBtnStop")
        self._toggle_btn.setStyle(self._toggle_btn.style())

        self._status_lbl.setText("● Monitoring active")
        self._status_lbl.setStyleSheet("color: #00f5ff;")

    def _stop(self):
        if self._camera_thread:
            self._camera_thread.stop()
            self._camera_thread = None

        self._is_monitoring = False
        self._toggle_btn.setText("▶  Start Monitoring")
        self._toggle_btn.setObjectName("toggleBtn")
        self._toggle_btn.setStyle(self._toggle_btn.style())

        self._status_lbl.setText("● Not monitoring")
        self._status_lbl.setStyleSheet("")

        self._camera_lbl.clear()
        self._camera_lbl.setText("Camera feed will appear here\nonce monitoring starts.")
        self._rate_lbl.setText("--")
        self._rate_lbl.setStyleSheet("")
        self._ear_val.setText("--")
        self._face_val.setText("Not detected")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @pyqtSlot(object, bool, float, bool)
    def _on_frame(self, frame, blink: bool, ear: float, face: bool):
        # Register blink
        if blink:
            self._monitor.register_blink()

        # Check if we should notify
        if self._monitor.should_notify():
            notifier.notify()

        # Update camera preview
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(
            self._camera_lbl.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._camera_lbl.setPixmap(pixmap)

        # EAR + face status (live, every frame)
        if face:
            color = "#00f5ff" if ear >= BlinkDetector.EAR_THRESHOLD else "#ff5555"
            self._ear_val.setText(f"{ear:.3f}")
            self._ear_val.setStyleSheet(f"color: {color};")
            self._face_val.setText("Detected ✓")
            self._face_val.setStyleSheet("color: #00f5ff;")
        else:
            self._ear_val.setText("--")
            self._ear_val.setStyleSheet("color: #555555;")
            self._face_val.setText("Not detected")
            self._face_val.setStyleSheet("color: #555555;")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self._status_lbl.setText(f"● Error: {msg}")
        self._status_lbl.setStyleSheet("color: #ff5555;")
        self._stop()

    def _refresh_stats(self):
        if not self._is_monitoring:
            return

        rate = self._monitor.get_blink_rate()
        if rate is None:
            self._rate_lbl.setText("…")
            self._rate_lbl.setStyleSheet("color: #555555; font-size: 64px; font-weight: 700;")
        else:
            self._rate_lbl.setText(f"{rate:.1f}")
            color = "#00f5ff" if rate >= 12 else "#ff5555"
            self._rate_lbl.setStyleSheet(f"color: {color}; font-size: 64px; font-weight: 700;")

        self._total_val.setText(str(self._monitor.total_blinks))

        secs = int(self._monitor.get_session_duration())
        self._time_val.setText(f"{secs // 60:02d}:{secs % 60:02d}")

    # ------------------------------------------------------------------
    # Window events
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        """Intercept close → minimize to tray instead."""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Blink",
            "Still running in the background. Right-click the tray icon to quit.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )

    def _quit(self):
        self._stop()
        self._detector.close()
        QApplication.instance().quit()
