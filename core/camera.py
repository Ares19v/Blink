"""
camera.py  v2
Signal now emits 5 values to match detector v2.
"""
import cv2
from PyQt6.QtCore import QThread, pyqtSignal

from core.detector import BlinkDetector
from core.logger_setup import logger


class CameraThread(QThread):
    # (annotated_frame, blink_detected, ear_value, face_detected, blink_duration_ms)
    frame_ready     = pyqtSignal(object, bool, float, bool, float)
    error_occurred  = pyqtSignal(str)

    def __init__(self, detector: BlinkDetector, camera_index: int = 0):
        super().__init__()
        self.detector = detector
        self.camera_index = camera_index
        self._running = False

    def run(self) -> None:
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            self.error_occurred.emit(f"Cannot open camera (index {self.camera_index})")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        logger.info(f"Camera {self.camera_index} opened")

        self._running = True
        while self._running:
            ret, frame = cap.read()
            if not ret:
                self.error_occurred.emit("Camera read failed — check connection")
                break
            frame = cv2.flip(frame, 1)
            annotated, blink, ear, face, dur_ms = self.detector.process(frame)
            self.frame_ready.emit(annotated, blink, ear, face, dur_ms)

        cap.release()
        logger.info("Camera released")

    def stop(self) -> None:
        self._running = False
        self.wait(3000)
