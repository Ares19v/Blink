"""
detector.py
MediaPipe FaceLandmarker (Tasks API) + Eye Aspect Ratio (EAR) blink detection.

mediapipe >= 0.10.30 uses mp.tasks.vision.FaceLandmarker.
The model file (~4 MB) is downloaded automatically from Google on first run
and cached in the project's models/ folder.
"""
import os
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# ------------------------------------------------------------------
# Model auto-download
# ------------------------------------------------------------------
_MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "face_landmarker.task")
_MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def _ensure_model():
    os.makedirs(_MODEL_DIR, exist_ok=True)
    if not os.path.exists(_MODEL_PATH):
        print("[detector] Downloading face_landmarker.task (~4 MB)…")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("[detector] Model downloaded.")


# ------------------------------------------------------------------
# Detector
# ------------------------------------------------------------------

class BlinkDetector:
    # FaceLandmarker landmark indices for each eye
    # (same as MediaPipe Face Mesh 478-point model)
    LEFT_EYE  = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33,  160, 158, 133, 153, 144]

    EAR_THRESHOLD = 0.21
    CONSEC_FRAMES = 2

    def __init__(self):
        _ensure_model()

        base_options = mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        self._frame_counter = 0
        self._blink_in_progress = False

    # ------------------------------------------------------------------

    @staticmethod
    def _ear(landmarks, indices) -> float:
        """landmarks: list of NormalizedLandmark (already 0-1 range)."""
        pts = [np.array([landmarks[i].x, landmarks[i].y]) for i in indices]
        A = np.linalg.norm(pts[1] - pts[5])
        B = np.linalg.norm(pts[2] - pts[4])
        C = np.linalg.norm(pts[0] - pts[3])
        return (A + B) / (2.0 * C) if C != 0 else 0.0

    def process(self, frame: np.ndarray):
        """
        Parameters
        ----------
        frame : BGR np.ndarray from OpenCV

        Returns
        -------
        annotated_frame, blink_detected, ear_value, face_detected
        """
        h, w = frame.shape[:2]

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
        )
        result = self._landmarker.detect(mp_image)

        blink_detected = False
        ear_value = 0.0

        if not result.face_landmarks:
            cv2.putText(frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (80, 80, 80), 2)
            self._frame_counter = 0
            self._blink_in_progress = False
            return frame, False, 0.0, False

        landmarks = result.face_landmarks[0]   # list of NormalizedLandmark

        left_ear  = self._ear(landmarks, self.LEFT_EYE)
        right_ear = self._ear(landmarks, self.RIGHT_EYE)
        ear_value = (left_ear + right_ear) / 2.0

        # Blink state machine
        if ear_value < self.EAR_THRESHOLD:
            self._frame_counter += 1
            self._blink_in_progress = True
        else:
            if self._blink_in_progress and self._frame_counter >= self.CONSEC_FRAMES:
                blink_detected = True
            self._frame_counter = 0
            self._blink_in_progress = False

        # Draw eye landmark dots (cyan)
        for idx in self.LEFT_EYE + self.RIGHT_EYE:
            lm = landmarks[idx]
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 2, (0, 245, 255), -1)

        # EAR overlay
        ear_color = (0, 245, 255) if ear_value >= self.EAR_THRESHOLD else (60, 60, 255)
        cv2.putText(frame, f"EAR: {ear_value:.3f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, ear_color, 2)
        if blink_detected:
            cv2.putText(frame, "BLINK!", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 245, 255), 2)

        return frame, blink_detected, ear_value, True

    def close(self):
        self._landmarker.close()
