"""
test_detector.py
pytest unit tests for BlinkDetector EAR logic.
Mocks the MediaPipe landmarker so no camera or model needed.
"""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from core.detector import BlinkDetector


# ------------------------------------------------------------------
# Test the EAR formula in isolation (pure math — no model needed)
# ------------------------------------------------------------------

def _make_landmark(x, y):
    lm = MagicMock()
    lm.x = x
    lm.y = y
    return lm


def _build_landmarks(pts):
    """pts: list of (x, y) in order of LEFT_EYE indices."""
    return [_make_landmark(x, y) for x, y in pts]


def test_ear_open_eye():
    """Wide open eye should have EAR well above 0.21."""
    # Points: left, top-left, top-right, right, bottom-right, bottom-left
    # Horizontal spread = 0.1, vertical spread = 0.03 → EAR ≈ 0.30
    pts = [(0.0, 0.0), (0.033, 0.03), (0.067, 0.03),
           (0.1, 0.0), (0.067, -0.03), (0.033, -0.03)]
    landmarks = _build_landmarks(pts)
    ear = BlinkDetector._ear(landmarks, list(range(6)))
    assert ear > 0.21, f"Expected open-eye EAR > 0.21, got {ear:.4f}"


def test_ear_closed_eye():
    """Closed eye: verticals collapse → EAR near zero."""
    pts = [(0.0, 0.0), (0.033, 0.001), (0.067, 0.001),
           (0.1, 0.0), (0.067, -0.001), (0.033, -0.001)]
    landmarks = _build_landmarks(pts)
    ear = BlinkDetector._ear(landmarks, list(range(6)))
    assert ear < 0.21, f"Expected closed-eye EAR < 0.21, got {ear:.4f}"


def test_ear_zero_horizontal_does_not_divide_by_zero():
    """If horizontal distance is 0, should return 0.0 gracefully."""
    pts = [(0.0, 0.0)] * 6
    landmarks = _build_landmarks(pts)
    ear = BlinkDetector._ear(landmarks, list(range(6)))
    assert ear == 0.0


# ------------------------------------------------------------------
# Test calibration logic (no model, no camera)
# ------------------------------------------------------------------

@patch("core.detector._ensure_model")
@patch("mediapipe.tasks.python.vision.FaceLandmarker.create_from_options")
def test_calibration_sets_threshold(mock_create, mock_ensure):
    mock_create.return_value = MagicMock()
    detector = BlinkDetector()

    detector.start_calibration()
    # Simulate 20 open-eye EAR readings of 0.30
    detector._calib_ears = [0.30] * 20
    threshold = detector.stop_calibration()

    expected = round(0.30 * 0.75, 4)
    assert abs(threshold - expected) < 0.001, \
        f"Expected threshold {expected:.4f}, got {threshold:.4f}"


@patch("core.detector._ensure_model")
@patch("mediapipe.tasks.python.vision.FaceLandmarker.create_from_options")
def test_calibration_fallback_with_no_data(mock_create, mock_ensure):
    mock_create.return_value = MagicMock()
    detector = BlinkDetector()

    detector.start_calibration()
    detector._calib_ears = []   # No data
    threshold = detector.stop_calibration()

    # Should fall back to whatever the threshold already was
    assert threshold == detector.ear_threshold
