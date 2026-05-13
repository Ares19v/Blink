"""
detector.py
MediaPipe FaceLandmarker + EAR blink detection.

New in v2:
- Adaptive EAR threshold via start_calibration() / stop_calibration()
- Blink duration tracking (ms)
- process() returns 5-tuple: (frame, blink, ear, face_detected, blink_duration_ms)
"""
import os
import time
import urllib.request

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from core.logger_setup import logger

_MODEL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "face_landmarker.task")
_MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def _ensure_model() -> None:
    os.makedirs(_MODEL_DIR, exist_ok=True)
    if not os.path.exists(_MODEL_PATH):
        logger.info("Downloading face_landmarker.task (~4 MB)…")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        logger.info("Model downloaded and cached.")


class BlinkDetector:
    LEFT_EYE  = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33,  160, 158, 133, 153, 144]

    DEFAULT_EAR_THRESHOLD = 0.21
    CONSEC_FRAMES = 2

    def __init__(self, ear_threshold: float | None = None):
        _ensure_model()
        base = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
        opts = mp_vision.FaceLandmarkerOptions(
            base_options=base,
            running_mode=mp_vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(opts)

        self.ear_threshold: float = ear_threshold if ear_threshold else self.DEFAULT_EAR_THRESHOLD
        self._frame_counter: int = 0
        self._blink_in_progress: bool = False
        self._blink_start_time: float | None = None
        self.last_blink_duration_ms: float = 0.0

        # Calibration
        self._calibrating: bool = False
        self._calib_ears: list[float] = []

    # ------------------------------------------------------------------
    # EAR
    # ------------------------------------------------------------------

    @staticmethod
    def _ear(landmarks, indices) -> float:
        pts = [np.array([landmarks[i].x, landmarks[i].y]) for i in indices]
        A = np.linalg.norm(pts[1] - pts[5])
        B = np.linalg.norm(pts[2] - pts[4])
        C = np.linalg.norm(pts[0] - pts[3])
        return (A + B) / (2.0 * C) if C != 0 else 0.0

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def start_calibration(self) -> None:
        self._calib_ears = []
        self._calibrating = True
        logger.info("EAR calibration started")

    def stop_calibration(self) -> float:
        """
        Stops calibration and returns the computed threshold.
        Falls back to DEFAULT_EAR_THRESHOLD if not enough data.
        """
        self._calibrating = False
        if len(self._calib_ears) < 10:
            logger.warning("Not enough calibration frames — using default threshold")
            return self.ear_threshold

        mean_ear = float(np.mean(self._calib_ears))
        self.ear_threshold = round(mean_ear * 0.75, 4)
        logger.info(f"Calibration done. mean EAR={mean_ear:.3f} → threshold={self.ear_threshold:.3f}")
        return self.ear_threshold

    # ------------------------------------------------------------------
    # Process
    # ------------------------------------------------------------------

    def process(self, frame: np.ndarray) -> tuple:
        """
        Returns
        -------
        (annotated_frame, blink_detected, ear_value, face_detected, blink_duration_ms)
        """
        h, w = frame.shape[:2]

        mp_img = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
        )
        result = self._landmarker.detect(mp_img)

        if not result.face_landmarks:
            self._frame_counter = 0
            self._blink_in_progress = False
            cv2.putText(frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (80, 80, 80), 2)
            return frame, False, 0.0, False, 0.0

        lm = result.face_landmarks[0]
        left_ear  = self._ear(lm, self.LEFT_EYE)
        right_ear = self._ear(lm, self.RIGHT_EYE)
        ear = (left_ear + right_ear) / 2.0

        # Feed calibration
        if self._calibrating and ear > 0.15:
            self._calib_ears.append(ear)

        # Blink state machine
        now = time.time()
        blink_detected = False
        blink_duration_ms = 0.0

        if ear < self.ear_threshold:
            if not self._blink_in_progress:
                self._blink_start_time = now
            self._frame_counter += 1
            self._blink_in_progress = True
        else:
            if self._blink_in_progress and self._frame_counter >= self.CONSEC_FRAMES:
                blink_detected = True
                if self._blink_start_time:
                    blink_duration_ms = (now - self._blink_start_time) * 1000.0
                    self.last_blink_duration_ms = blink_duration_ms
                    logger.debug(f"Blink: {blink_duration_ms:.1f} ms, EAR={ear:.3f}")
            self._frame_counter = 0
            self._blink_in_progress = False
            self._blink_start_time = None

        # Draw landmarks
        for idx in self.LEFT_EYE + self.RIGHT_EYE:
            x = int(lm[idx].x * w)
            y = int(lm[idx].y * h)
            cv2.circle(frame, (x, y), 2, (0, 245, 255), -1)

        # Overlays
        ear_color = (0, 245, 255) if ear >= self.ear_threshold else (60, 60, 255)
        cv2.putText(frame, f"EAR: {ear:.3f}  Thr: {self.ear_threshold:.3f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, ear_color, 2)
        if blink_detected:
            cv2.putText(frame, f"BLINK! ({blink_duration_ms:.0f}ms)", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 245, 255), 2)

        return frame, blink_detected, ear, True, blink_duration_ms

    def close(self) -> None:
        self._landmarker.close()
