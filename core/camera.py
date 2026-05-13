"""
camera.py
OpenCV camera capture running in a QThread.
Emits a signal for every processed frame so the GUI stays responsive.
"""
import cv2
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np

from core.detector import BlinkDetector


class CameraThread(QThread):
    # Signals emitted every frame
    frame_ready = pyqtSignal(object, bool, float, bool)
    # (annotated_frame, blink_detected, ear_value, face_detected)

    error_occurred = pyqtSignal(str)

    def __init__(self, detector: BlinkDetector, camera_index: int = 0):
        super().__init__()
        self.detector = detector
        self.camera_index = camera_index
        self._running = False

    def run(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            self.error_occurred.emit(f"Could not open camera (index {self.camera_index})")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        self._running = True

        while self._running:
            ret, frame = cap.read()
            if not ret:
                self.error_occurred.emit("Camera read failed — is the camera unplugged?")
                break

            # Mirror horizontally so it feels natural (like a selfie cam)
            frame = cv2.flip(frame, 1)

            annotated, blink, ear, face_detected = self.detector.process(frame)
            self.frame_ready.emit(annotated, blink, ear, face_detected)

        cap.release()

    def stop(self):
        self._running = False
        self.wait(3000)  # wait up to 3s for thread to finish
