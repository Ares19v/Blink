"""
blink_monitor.py
Maintains a rolling 60-second window of blink timestamps and computes
blink rate (blinks/min). Triggers a notification callback when rate is low.
"""
import time
from collections import deque


class BlinkMonitor:
    def __init__(
        self,
        window_seconds: int = 60,
        low_rate_threshold: float = 12.0,  # blinks/min — below this → alert
        notification_cooldown: float = 90.0,  # seconds between notifications
    ):
        self.window_seconds = window_seconds
        self.low_rate_threshold = low_rate_threshold
        self.notification_cooldown = notification_cooldown

        self._blink_timestamps: deque = deque()
        self._last_notification_time: float = 0.0
        self._session_start: float = time.time()
        self.total_blinks: int = 0

    # ------------------------------------------------------------------

    def register_blink(self):
        """Call this every time a blink is detected."""
        now = time.time()
        self._blink_timestamps.append(now)
        self.total_blinks += 1
        self._evict_old(now)

    def get_blink_rate(self) -> float | None:
        """
        Returns blinks per minute, or None if not enough data yet
        (less than 10 seconds of session time).
        """
        now = time.time()
        self._evict_old(now)

        elapsed_session = now - self._session_start
        if elapsed_session < 10:
            return None  # Too early to give a meaningful rate

        # Use the smaller of elapsed_session and window_seconds as the denominator
        window = min(elapsed_session, float(self.window_seconds))
        rate = (len(self._blink_timestamps) / window) * 60.0
        return rate

    def should_notify(self) -> bool:
        """
        Returns True if blink rate is low AND enough cooldown has passed
        since the last notification.
        """
        rate = self.get_blink_rate()
        if rate is None:
            return False

        now = time.time()
        if rate < self.low_rate_threshold:
            if (now - self._last_notification_time) >= self.notification_cooldown:
                self._last_notification_time = now
                return True
        return False

    def get_session_duration(self) -> float:
        """Returns session duration in seconds."""
        return time.time() - self._session_start

    def reset(self):
        self._blink_timestamps.clear()
        self.total_blinks = 0
        self._session_start = time.time()
        self._last_notification_time = 0.0

    # ------------------------------------------------------------------

    def _evict_old(self, now: float):
        cutoff = now - self.window_seconds
        while self._blink_timestamps and self._blink_timestamps[0] < cutoff:
            self._blink_timestamps.popleft()
