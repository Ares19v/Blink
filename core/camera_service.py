"""
camera_service.py
High-performance, low-latency background camera service for Blink.
Uses DirectShow (CAP_DSHOW) on Windows with a dedicated VideoStream thread
and WebSocket base64 streaming matching the architecture of Inspection-Engine.
"""

import base64
import sys
import threading
import time
from datetime import datetime
from typing import Callable, Optional, Set

import cv2

from core.blink_monitor import BlinkMonitor
from core.config_manager import load_config, save_config
from core.database import init_db, save_session
from core.detector import BlinkDetector
from core.logger_setup import logger
from core import notifier


class VideoStream:
    """Multi-threaded OpenCV camera grabber to eliminate frame buffering delay."""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        if sys.platform == "win32":
            # On Windows, DSHOW is significantly faster with lower latency than MSMF
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(camera_index)
            try:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            except Exception:
                pass
        else:
            self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera (index {camera_index})")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 60)

        self.ret, self.frame = self.cap.read()
        self.stopped = False


    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()
            if not self.ret:
                time.sleep(0.005)

    def read(self):
        return self.frame if self.ret else None

    def stop(self):
        self.stopped = True
        self.cap.release()


class CameraService:
    LIVE_JPEG_QUALITY = 55


    def __init__(self):
        init_db()
        self._cfg = load_config()

        self.detector = BlinkDetector(
            ear_threshold=self._cfg.get(
                "ear_threshold", BlinkDetector.DEFAULT_EAR_THRESHOLD
            )
        )
        self.monitor = BlinkMonitor(
            low_rate_threshold=self._cfg.get("blink_rate_threshold", 12.0),
            notification_cooldown=self._cfg.get("notification_cooldown", 90),
        )

        self.camera_index: int = self._cfg.get("camera_index", 0)
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stream: Optional[VideoStream] = None
        self._lock = threading.Lock()

        # Cached latest frame & stats
        self._latest_jpeg: Optional[bytes] = None
        self._latest_b64: str = ""
        self._latest_stats: dict = {
            "is_monitoring": False,
            "face_detected": False,
            "ear": 0.0,
            "ear_threshold": self.detector.ear_threshold,
            "blink_detected": False,
            "blink_duration_ms": 0.0,
            "blink_rate": 0.0,
            "fatigue_score": 0.0,
            "total_blinks": 0,
            "session_duration_sec": 0,
            "twenty_countdown_sec": 0,
            "calibrating": False,
            "calibration_progress": 0,
            "image": "",
        }

        self._session_start_time: Optional[datetime] = None
        self._session_start_timestamp: float = 0.0

        # 20-20-20 timer
        self._twenty_interval = self._cfg.get("twenty_twenty_twenty_interval_sec", 1200)
        self._twenty_enabled = self._cfg.get("twenty_twenty_twenty_enabled", True)
        self._twenty_next_alert_time: float = 0.0

        # Calibration state
        self._calibration_start_time: float = 0.0
        self._calibration_duration: float = 7.0
        self._calibrating: bool = False

        # Telemetry subscribers
        self._listeners: Set[Callable[[dict], None]] = set()

    def reload_config(self) -> None:
        self._cfg = load_config()
        self.camera_index = self._cfg.get("camera_index", 0)
        self.detector.ear_threshold = self._cfg.get(
            "ear_threshold", BlinkDetector.DEFAULT_EAR_THRESHOLD
        )
        self.monitor.low_rate_threshold = self._cfg.get("blink_rate_threshold", 12.0)
        self.monitor.notification_cooldown = self._cfg.get("notification_cooldown", 90)
        self._twenty_interval = self._cfg.get("twenty_twenty_twenty_interval_sec", 1200)
        self._twenty_enabled = self._cfg.get("twenty_twenty_twenty_enabled", True)

    def is_running(self) -> bool:
        return self._running

    def start_monitoring(self, camera_index: Optional[int] = None) -> bool:
        with self._lock:
            if self._running:
                return True

            if camera_index is not None:
                self.camera_index = camera_index

            self.reload_config()
            self.monitor.reset()
            self._session_start_time = datetime.now()
            self._session_start_timestamp = time.time()
            self._twenty_next_alert_time = (
                time.time() + self._twenty_interval if self._twenty_enabled else 0.0
            )

            try:
                self._stream = VideoStream(self.camera_index).start()
            except Exception as exc:
                logger.error(f"Failed to initialize VideoStream: {exc}")
                return False

            self._running = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
            logger.info(f"High-speed monitoring started on camera {self.camera_index}")
            return True

    def stop_monitoring(self) -> dict:
        with self._lock:
            if not self._running:
                return self._latest_stats

            self._running = False
            if self._stream:
                self._stream.stop()
                self._stream = None

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.5)

            # Record session to SQLite
            if self._session_start_time:
                end_time = datetime.now()
                dur_secs = (end_time - self._session_start_time).total_seconds()
                total_blinks = self.monitor.total_blinks
                avg_rate = self.monitor.get_blink_rate() or 0.0
                avg_fatigue = self.monitor.get_avg_fatigue_score()
                avg_duration = self.monitor.get_avg_blink_duration_ms()

                if dur_secs >= 5:
                    save_session(
                        start_time=self._session_start_time,
                        end_time=end_time,
                        duration_secs=dur_secs,
                        total_blinks=total_blinks,
                        avg_blink_rate=round(avg_rate, 1),
                        avg_fatigue_score=round(avg_fatigue, 1),
                        avg_blink_duration_ms=round(avg_duration, 1),
                        ear_threshold=self.detector.ear_threshold,
                    )
                    logger.info("Session persisted to database.")

            self._latest_stats["is_monitoring"] = False
            self._latest_stats["face_detected"] = False
            self._latest_stats["image"] = ""
            self._latest_b64 = ""
            logger.info("Monitoring stopped.")
            return self._latest_stats

    def start_calibration(self) -> None:
        self._calibrating = True
        self._calibration_start_time = time.time()
        self.detector.start_calibration()
        logger.info("Calibration started in camera service")

    def stop_calibration(self) -> float:
        self._calibrating = False
        new_thresh = self.detector.stop_calibration()
        self._cfg["ear_threshold"] = new_thresh
        self._cfg["calibrated"] = True
        save_config(self._cfg)
        logger.info(f"Calibration completed with threshold {new_thresh}")
        return new_thresh

    def get_calibration_status(self) -> dict:
        if not self._calibrating:
            return {
                "calibrating": False,
                "progress": 100 if self._cfg.get("calibrated", False) else 0,
                "ear_threshold": self.detector.ear_threshold,
                "samples_count": len(self.detector._calib_ears),
            }
        elapsed = time.time() - self._calibration_start_time
        progress = min(100, int((elapsed / self._calibration_duration) * 100))
        return {
            "calibrating": True,
            "progress": progress,
            "ear_threshold": self.detector.ear_threshold,
            "samples_count": len(self.detector._calib_ears),
            "current_mean": round(
                float(sum(self.detector._calib_ears) / len(self.detector._calib_ears)), 3
            )
            if self.detector._calib_ears
            else 0.0,
        }

    def get_latest_jpeg(self) -> Optional[bytes]:
        return self._latest_jpeg

    def get_stats(self) -> dict:
        return self._latest_stats.copy()

    def add_listener(self, callback: Callable[[dict], None]) -> None:
        self._listeners.add(callback)

    def remove_listener(self, callback: Callable[[dict], None]) -> None:
        self._listeners.discard(callback)

    def _notify_listeners(self, stats: dict) -> None:
        for cb in list(self._listeners):
            try:
                cb(stats)
            except Exception as e:
                logger.debug(f"Telemetry listener error: {e}")

    def _worker(self) -> None:
        while self._running and self._stream:
            raw_frame = self._stream.read()
            if raw_frame is None:
                time.sleep(0.005)
                continue

            frame = cv2.flip(raw_frame, 1)
            annotated, blink, ear, face_detected, dur_ms = self.detector.process(frame)

            now = time.time()

            # Calibration auto-finish check
            if self._calibrating:
                if (now - self._calibration_start_time) >= self._calibration_duration:
                    self.stop_calibration()

            # Update monitor
            if blink:
                self.monitor.register_blink(dur_ms)
            if face_detected and ear > 0:
                self.monitor.register_ear(ear)

            # Notifications
            if self.monitor.should_notify():
                if self._cfg.get("sound_enabled", True):
                    notifier.notify(
                        title="Blink Reminder 👁️",
                        message="Your blink rate is low. Rest or blink consciously!",
                        beep_count=1,
                    )

            # 20-20-20 Break Check
            twenty_remaining = 0
            if self._twenty_enabled and self._twenty_next_alert_time > 0:
                twenty_remaining = max(0, int(self._twenty_next_alert_time - now))
                if twenty_remaining <= 0:
                    self._twenty_next_alert_time = now + self._twenty_interval
                    if self._cfg.get("sound_enabled", True):
                        notifier.notify(
                            title="20-20-20 Break Reminder 🌿",
                            message="Look at an object 20 feet away for 20 seconds!",
                            beep_count=2,
                        )

            rate = self.monitor.get_blink_rate()
            fatigue = self.monitor.get_fatigue_score()

            # Encode frame to JPEG with optimized quality for real-time WebSocket transfer
            ret, buf = cv2.imencode(
                ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, self.LIVE_JPEG_QUALITY]
            )
            if ret:
                self._latest_jpeg = buf.tobytes()
                self._latest_b64 = base64.b64encode(self._latest_jpeg).decode("utf-8")

            stats = {
                "is_monitoring": True,
                "face_detected": face_detected,
                "ear": round(ear, 3),
                "ear_threshold": round(self.detector.ear_threshold, 3),
                "blink_detected": blink,
                "blink_duration_ms": round(dur_ms, 1),
                "blink_rate": round(rate, 1) if rate is not None else None,
                "fatigue_score": round(fatigue, 1) if fatigue is not None else None,
                "total_blinks": self.monitor.total_blinks,
                "session_duration_sec": int(now - self._session_start_timestamp),
                "twenty_countdown_sec": twenty_remaining,
                "calibrating": self._calibrating,
                "calibration_progress": self.get_calibration_status()["progress"]
                if self._calibrating
                else 0,
                "image": self._latest_b64,
            }

            self._latest_stats = stats
            self._notify_listeners(stats)

            # Cap loop with minimal sleep to allow OS yield without stalling throughput
            time.sleep(0.002)


        logger.info("Camera worker loop exited.")


# Global singleton instance
camera_service = CameraService()
