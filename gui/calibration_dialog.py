"""
calibration_dialog.py
Startup modal: 7-second countdown while face is tracked.
Returns the calibrated EAR threshold on accept.
"""
import cv2
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap

from core.camera import CameraThread
from core.detector import BlinkDetector
from core.logger_setup import logger


class CalibrationDialog(QDialog):
    CALIBRATION_SECS = 7

    def __init__(self, detector: BlinkDetector, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Blink — Calibration")
        self.setFixedSize(560, 460)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setStyleSheet("""
            QDialog  { background:#0a0a0a; color:#e0e0e0; font-family:'Segoe UI'; }
            QLabel   { color:#e0e0e0; }
            QLabel#title { color:#00f5ff; font-size:18px; font-weight:700; }
            QLabel#sub   { color:#888888; font-size:12px; }
            QLabel#cam   { background:#080808; border-radius:6px; }
            QProgressBar { border:1px solid #1e1e1e; border-radius:4px;
                           background:#111; height:14px; text-align:center; color:#fff; }
            QProgressBar::chunk { background:#00f5ff; border-radius:4px; }
            QPushButton  { background:#00f5ff; color:#000; border:none; border-radius:6px;
                           padding:10px 20px; font-weight:700; }
            QPushButton:hover { background:#33f7ff; }
            QPushButton:disabled { background:#1a1a1a; color:#555; }
        """)

        self._detector    = detector
        self._cam_index   = camera_index
        self._cam_thread: CameraThread | None = None
        self._elapsed     = 0
        self._done        = False
        self.calibrated_threshold: float = detector.DEFAULT_EAR_THRESHOLD

        self._build_ui()
        self._start_camera()

        self._countdown = QTimer(self)
        self._countdown.timeout.connect(self._tick)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Eye Calibration")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel(
            "Sit naturally, look at the screen and keep your eyes open.\n"
            "Calibration takes 7 seconds."
        )
        sub.setObjectName("sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        self._cam_lbl = QLabel()
        self._cam_lbl.setObjectName("cam")
        self._cam_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cam_lbl.setFixedHeight(300)
        lay.addWidget(self._cam_lbl)

        self._progress = QProgressBar()
        self._progress.setRange(0, self.CALIBRATION_SECS)
        self._progress.setValue(0)
        lay.addWidget(self._progress)

        self._status_lbl = QLabel("Waiting for face…")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._status_lbl)

        self._done_btn = QPushButton("Starting…")
        self._done_btn.setEnabled(False)
        self._done_btn.clicked.connect(self._finish)
        lay.addWidget(self._done_btn)

    # ------------------------------------------------------------------
    def _start_camera(self) -> None:
        self._detector.start_calibration()
        self._cam_thread = CameraThread(self._detector, self._cam_index)
        self._cam_thread.frame_ready.connect(self._on_frame)
        self._cam_thread.start()
        self._countdown.start(1000)

    @pyqtSlot(object, bool, float, bool, float)
    def _on_frame(self, frame, blink, ear, face, dur) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self._cam_lbl.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._cam_lbl.setPixmap(pix)

        if face:
            self._status_lbl.setText(f"Face detected — EAR: {ear:.3f}")
        else:
            self._status_lbl.setText("⚠ No face detected — please centre your face")

    def _tick(self) -> None:
        self._elapsed += 1
        self._progress.setValue(self._elapsed)
        if self._elapsed >= self.CALIBRATION_SECS:
            self._countdown.stop()
            self._finish_calibration()

    def _finish_calibration(self) -> None:
        threshold = self._detector.stop_calibration()
        self.calibrated_threshold = threshold
        self._status_lbl.setText(
            f"✓ Calibrated! EAR threshold set to {threshold:.3f}"
        )
        self._done_btn.setText("Continue →")
        self._done_btn.setEnabled(True)
        logger.info(f"Calibration dialog: threshold={threshold:.3f}")

    def _finish(self) -> None:
        if self._cam_thread:
            self._cam_thread.stop()
            self._cam_thread = None
        self.accept()

    def closeEvent(self, event) -> None:
        if self._cam_thread:
            self._cam_thread.stop()
        super().closeEvent(event)
