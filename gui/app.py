"""
app.py  v2
Main window — ties together all new features:
  - Calibration dialog on first launch
  - Fatigue score + blink duration stat cards
  - 20-20-20 timer (2 beeps)
  - Settings dialog
  - History window
  - SQLite session save on stop
Same black / cyan / white color scheme.
"""

import cv2
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QAction

from core.camera import CameraThread
from core.detector import BlinkDetector
from core.blink_monitor import BlinkMonitor
from core.config_manager import load_config, save_config
from core import notifier
from core.database import init_db, save_session
from core.logger_setup import logger

from gui.calibration_dialog import CalibrationDialog
from gui.settings_dialog import SettingsDialog
from gui.history_widget import HistoryWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blink — Eye Health Monitor")
        self.setMinimumSize(1020, 600)

        # Init DB and load config
        init_db()
        self._cfg = load_config()

        # Core objects
        self._detector = BlinkDetector(
            ear_threshold=self._cfg.get(
                "ear_threshold", BlinkDetector.DEFAULT_EAR_THRESHOLD
            )
        )
        self._monitor = BlinkMonitor(
            low_rate_threshold=self._cfg.get("blink_rate_threshold", 12.0),
            notification_cooldown=self._cfg.get("notification_cooldown", 90),
        )

        self._camera_thread: CameraThread | None = None
        self._is_monitoring = False
        self._session_start: datetime | None = None

        # History window (lazy)
        self._history_win: HistoryWidget | None = None

        self._build_ui()
        self._build_tray()
        self._load_stylesheet()

        # Stats refresh timer (1 s)
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(1000)

        # 20-20-20 timer
        self._twenty_timer = QTimer(self)
        self._twenty_timer.timeout.connect(self._on_twenty_twenty_twenty)
        self._twenty_elapsed = QTimer(self)
        self._twenty_elapsed.timeout.connect(self._update_twenty_countdown)
        self._twenty_remaining_sec = 0

        # Run calibration on first use (or if not yet calibrated)
        if not self._cfg.get("calibrated", False):
            QTimer.singleShot(300, self._run_calibration)

        logger.info("MainWindow initialised")

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        lay = QHBoxLayout(root)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(16)
        lay.addWidget(self._build_camera_panel(), stretch=3)
        lay.addWidget(self._build_stats_panel(), stretch=1)

    # ---- Left: camera ----

    def _build_camera_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("cameraPanel")
        vbox = QVBoxLayout(panel)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        self._cam_lbl = QLabel("Camera feed will appear here\nonce monitoring starts.")
        self._cam_lbl.setObjectName("cameraLabel")
        self._cam_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cam_lbl.setMinimumSize(640, 450)
        vbox.addWidget(self._cam_lbl)

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
        vbox.setSpacing(10)

        # Title
        title = QLabel("BLINK")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)

        sub = QLabel("Eye Health Monitor")
        sub.setObjectName("appSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(sub)

        vbox.addSpacing(8)

        # Big blink rate
        self._rate_lbl = QLabel("--")
        self._rate_lbl.setObjectName("blinkRateBig")
        self._rate_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self._rate_lbl)

        unit = QLabel("blinks / min")
        unit.setObjectName("statUnit")
        unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(unit)

        vbox.addSpacing(6)

        # Stat cards
        self._ear_val, ear_card = self._stat_card("EAR Value", "--")
        self._fatigue_val, fatigue_card = self._stat_card("Fatigue Score", "--")
        self._dur_val, dur_card = self._stat_card("Avg Blink Duration", "--")
        self._total_val, total_card = self._stat_card("Total Blinks", "0")
        self._time_val, time_card = self._stat_card("Session Time", "00:00")
        self._face_val, face_card = self._stat_card("Face", "Not detected")

        for card in (
            ear_card,
            fatigue_card,
            dur_card,
            total_card,
            time_card,
            face_card,
        ):
            vbox.addWidget(card)

        # 20-20-20 countdown
        self._twenty_lbl = QLabel("")
        self._twenty_lbl.setObjectName("twentyLbl")
        self._twenty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self._twenty_lbl)

        vbox.addStretch()

        # Action buttons row
        btn_row = QHBoxLayout()
        self._settings_btn = QPushButton("⚙  Settings")
        self._settings_btn.setObjectName("secondaryBtn")
        self._settings_btn.clicked.connect(self._open_settings)
        btn_row.addWidget(self._settings_btn)

        self._history_btn = QPushButton("📊  History")
        self._history_btn.setObjectName("secondaryBtn")
        self._history_btn.clicked.connect(self._open_history)
        btn_row.addWidget(self._history_btn)

        self._calib_btn = QPushButton("🎯  Recalibrate")
        self._calib_btn.setObjectName("secondaryBtn")
        self._calib_btn.clicked.connect(self._run_calibration)
        btn_row.addWidget(self._calib_btn)

        vbox.addLayout(btn_row)

        # Start/Stop
        self._toggle_btn = QPushButton("▶  Start Monitoring")
        self._toggle_btn.setObjectName("toggleBtn")
        self._toggle_btn.clicked.connect(self._on_toggle)
        vbox.addWidget(self._toggle_btn)

        return panel

    @staticmethod
    def _stat_card(label_text: str, initial: str) -> tuple:
        card = QFrame()
        card.setObjectName("statCard")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(12, 6, 12, 6)
        vbox.setSpacing(1)
        lbl = QLabel(label_text.upper())
        lbl.setObjectName("statLabel")
        val = QLabel(initial)
        val.setObjectName("statValue")
        vbox.addWidget(lbl)
        vbox.addWidget(val)
        return val, card

    # ==================================================================
    # Stylesheet
    # ==================================================================

    def _load_stylesheet(self) -> None:
        import os

        qss = os.path.join(os.path.dirname(__file__), "theme.qss")
        try:
            with open(qss, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.warning("theme.qss not found")

    # ==================================================================
    # System Tray
    # ==================================================================

    def _build_tray(self) -> None:
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(
            self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        )
        self._tray.setToolTip("Blink — Eye Health Monitor")
        menu = QMenu()
        QAction_show = QAction("Show / Hide", self)
        QAction_show.triggered.connect(self._toggle_window)
        QAction_quit = QAction("Quit Blink", self)
        QAction_quit.triggered.connect(self._quit)
        menu.addAction(QAction_show)
        menu.addSeparator()
        menu.addAction(QAction_quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _toggle_window(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    # ==================================================================
    # Calibration
    # ==================================================================

    def _run_calibration(self) -> None:
        was_monitoring = self._is_monitoring
        if was_monitoring:
            self._stop()

        dlg = CalibrationDialog(
            self._detector,
            camera_index=self._cfg.get("camera_index", 0),
            parent=self,
        )
        if dlg.exec():
            threshold = dlg.calibrated_threshold
            self._detector.ear_threshold = threshold
            self._cfg["ear_threshold"] = threshold
            self._cfg["calibrated"] = True
            save_config(self._cfg)
            logger.info(f"EAR threshold updated to {threshold:.3f}")

        if was_monitoring:
            self._start()

    # ==================================================================
    # Monitoring control
    # ==================================================================

    def _on_toggle(self) -> None:
        if not self._is_monitoring:
            self._start()
        else:
            self._stop()

    def _start(self) -> None:
        self._monitor.low_rate_threshold = self._cfg.get("blink_rate_threshold", 12.0)
        self._monitor.notification_cooldown = self._cfg.get("notification_cooldown", 90)
        self._monitor.reset()
        self._session_start = datetime.now()

        self._camera_thread = CameraThread(
            self._detector,
            camera_index=self._cfg.get("camera_index", 0),
        )
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.error_occurred.connect(self._on_error)
        self._camera_thread.start()

        self._is_monitoring = True
        self._toggle_btn.setText("■  Stop Monitoring")
        self._toggle_btn.setObjectName("toggleBtnStop")
        self._toggle_btn.setStyle(self._toggle_btn.style())
        self._status_lbl.setText("● Monitoring active")
        self._status_lbl.setStyleSheet("color:#00f5ff;")

        # 20-20-20 timer
        if self._cfg.get("twenty_twenty_twenty_enabled", True):
            interval_sec = self._cfg.get("twenty_twenty_twenty_interval_sec", 1200)
            self._twenty_remaining_sec = interval_sec
            self._twenty_timer.start(interval_sec * 1000)
            self._twenty_elapsed.start(1000)
            self._update_twenty_countdown()

        logger.info("Monitoring started")

    def _stop(self) -> None:
        if self._camera_thread:
            self._camera_thread.stop()
            self._camera_thread = None

        self._twenty_timer.stop()
        self._twenty_elapsed.stop()
        self._twenty_lbl.setText("")

        # Save session
        if self._session_start:
            self._save_session()
            self._session_start = None

        self._is_monitoring = False
        self._toggle_btn.setText("▶  Start Monitoring")
        self._toggle_btn.setObjectName("toggleBtn")
        self._toggle_btn.setStyle(self._toggle_btn.style())
        self._status_lbl.setText("● Not monitoring")
        self._status_lbl.setStyleSheet("")

        self._cam_lbl.clear()
        self._cam_lbl.setText("Camera feed will appear here\nonce monitoring starts.")
        self._rate_lbl.setText("--")
        self._rate_lbl.setStyleSheet("")
        self._ear_val.setText("--")
        self._fatigue_val.setText("--")
        self._dur_val.setText("--")
        self._face_val.setText("Not detected")

        logger.info("Monitoring stopped")

    def _save_session(self) -> None:
        try:
            save_session(
                start_time=self._session_start,
                end_time=datetime.now(),
                duration_secs=self._monitor.get_session_duration(),
                total_blinks=self._monitor.total_blinks,
                avg_blink_rate=self._monitor.get_blink_rate() or 0.0,
                avg_fatigue_score=self._monitor.get_avg_fatigue_score(),
                avg_blink_duration_ms=self._monitor.get_avg_blink_duration_ms(),
                ear_threshold=self._detector.ear_threshold,
            )
            logger.info("Session saved to DB")
        except Exception as exc:
            logger.error(f"Failed to save session: {exc}")

    # ==================================================================
    # Slots
    # ==================================================================

    @pyqtSlot(object, bool, float, bool, float)
    def _on_frame(
        self, frame, blink: bool, ear: float, face: bool, dur_ms: float
    ) -> None:
        if blink:
            self._monitor.register_blink(dur_ms)
        if ear > 0:
            self._monitor.register_ear(ear)

        if self._monitor.should_notify():
            notifier.notify(
                "Blink! 👁️",
                "Hey! Don't forget to blink.",
                beep_count=1,
            )

        # Camera preview
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self._cam_lbl.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._cam_lbl.setPixmap(pix)

        # EAR + face (live, every frame)
        if face:
            c = "#00f5ff" if ear >= self._detector.ear_threshold else "#ff5555"
            self._ear_val.setText(f"{ear:.3f}")
            self._ear_val.setStyleSheet(f"color:{c};")
            self._face_val.setText("Detected ✓")
            self._face_val.setStyleSheet("color:#00f5ff;")
        else:
            self._ear_val.setText("--")
            self._ear_val.setStyleSheet("color:#555555;")
            self._face_val.setText("Not detected")
            self._face_val.setStyleSheet("color:#555555;")

        # Blink duration (live)
        if dur_ms > 0:
            quality = "Complete" if dur_ms >= 100 else "Partial"
            self._dur_val.setText(f"{dur_ms:.0f} ms  ({quality})")
            self._dur_val.setStyleSheet(
                "color:#00f5ff;" if dur_ms >= 100 else "color:#ffaa00;"
            )

    @pyqtSlot(str)
    def _on_error(self, msg: str) -> None:
        self._status_lbl.setText(f"● Error: {msg}")
        self._status_lbl.setStyleSheet("color:#ff5555;")
        logger.error(f"Camera error: {msg}")
        self._stop()

    def _refresh_stats(self) -> None:
        if not self._is_monitoring:
            return

        rate = self._monitor.get_blink_rate()
        if rate is None:
            self._rate_lbl.setText("…")
            self._rate_lbl.setStyleSheet(
                "color:#555555; font-size:64px; font-weight:700;"
            )
        else:
            self._rate_lbl.setText(f"{rate:.1f}")
            color = "#00f5ff" if rate >= self._monitor.low_rate_threshold else "#ff5555"
            self._rate_lbl.setStyleSheet(
                f"color:{color}; font-size:64px; font-weight:700;"
            )

        self._total_val.setText(str(self._monitor.total_blinks))

        secs = int(self._monitor.get_session_duration())
        self._time_val.setText(f"{secs // 60:02d}:{secs % 60:02d}")

        fatigue = self._monitor.get_fatigue_score()
        if fatigue is not None:
            fc = "#00f5ff" if fatigue < 40 else "#ffaa00" if fatigue < 70 else "#ff5555"
            self._fatigue_val.setText(f"{fatigue:.0f} / 100")
            self._fatigue_val.setStyleSheet(f"color:{fc};")

    def _update_twenty_countdown(self) -> None:
        if self._twenty_remaining_sec > 0:
            self._twenty_remaining_sec -= 1
        m = self._twenty_remaining_sec // 60
        s = self._twenty_remaining_sec % 60
        self._twenty_lbl.setText(f"👁️  Next break in {m:02d}:{s:02d}")

    def _on_twenty_twenty_twenty(self) -> None:
        interval = self._cfg.get("twenty_twenty_twenty_interval_sec", 1200)
        self._twenty_remaining_sec = interval
        notifier.notify(
            "Time for a break! 👁️",
            "Look 20 feet away for 20 seconds (20-20-20 rule).",
            beep_count=2,
        )
        logger.info("20-20-20 reminder fired")

    # ==================================================================
    # Settings / History
    # ==================================================================

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._cfg, parent=self)
        if dlg.exec():
            self._cfg = dlg.get_config()
            if self._is_monitoring:
                self._monitor.low_rate_threshold = self._cfg["blink_rate_threshold"]
                self._monitor.notification_cooldown = self._cfg["notification_cooldown"]
            logger.info("Settings applied")

    def _open_history(self) -> None:
        if self._history_win is None:
            self._history_win = HistoryWidget()
        else:
            self._history_win._load_data()
        self._history_win.show()
        self._history_win.raise_()

    # ==================================================================
    # Window events
    # ==================================================================

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Blink",
            "Still running. Right-click the tray icon to quit.",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )

    def _quit(self) -> None:
        self._stop()
        self._detector.close()
        logger.info("Application quit")
        QApplication.instance().quit()
