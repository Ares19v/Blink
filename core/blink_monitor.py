"""
blink_monitor.py  v2
Rolling window stats + fatigue score.
"""
import time
from collections import deque

import numpy as np

from core.logger_setup import logger


class BlinkMonitor:
    def __init__(
        self,
        window_seconds: int = 60,
        low_rate_threshold: float = 12.0,
        notification_cooldown: float = 90.0,
    ):
        self.window_seconds = window_seconds
        self.low_rate_threshold = low_rate_threshold
        self.notification_cooldown = notification_cooldown

        self._blink_times: deque   = deque()   # timestamps
        self._blink_durs:  deque   = deque()   # (timestamp, duration_ms) pairs
        self._ear_buf:     deque   = deque(maxlen=300)  # ~10 s at 30 fps
        self._fatigue_buf: deque   = deque(maxlen=60)

        self._last_notif:  float   = 0.0
        self._session_start: float = time.time()
        self.total_blinks: int     = 0

    # ------------------------------------------------------------------
    # Register events
    # ------------------------------------------------------------------

    def register_blink(self, duration_ms: float = 0.0) -> None:
        now = time.time()
        self._blink_times.append(now)
        self._blink_durs.append((now, duration_ms))
        self.total_blinks += 1
        self._evict(now)

    def register_ear(self, ear: float) -> None:
        if ear > 0:
            self._ear_buf.append(ear)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_blink_rate(self) -> float | None:
        """Blinks per minute — None if < 10 s of data."""
        now = time.time()
        self._evict(now)
        elapsed = now - self._session_start
        if elapsed < 10:
            return None
        window = min(elapsed, float(self.window_seconds))
        return (len(self._blink_times) / window) * 60.0

    def get_avg_blink_duration_ms(self) -> float:
        valid = [d for _, d in self._blink_durs if d > 0]
        return float(np.mean(valid)) if valid else 0.0

    def get_ear_variance(self) -> float:
        if len(self._ear_buf) < 30:
            return 0.0
        return float(np.var(list(self._ear_buf)))

    def get_fatigue_score(self) -> float | None:
        """
        0 = fully rested, 100 = severely fatigued.
        40% blink rate + 40% blink duration + 20% EAR variance.
        """
        rate = self.get_blink_rate()
        if rate is None:
            return None

        # Rate component: 0 blinks/min → 100, ≥20 → 0
        rate_c = max(0.0, min(100.0, (1.0 - rate / 20.0) * 100.0))

        # Duration component: <50 ms → 100, ≥250 ms → 0
        avg_dur = self.get_avg_blink_duration_ms()
        if avg_dur == 0:
            dur_c = 50.0  # neutral when no data yet
        else:
            dur_c = max(0.0, min(100.0, (1.0 - (avg_dur - 50.0) / 200.0) * 100.0))

        # Variance component: 0 → 0, ≥0.01 → 100
        var_c = min(100.0, self.get_ear_variance() * 10_000.0)

        score = 0.4 * rate_c + 0.4 * dur_c + 0.2 * var_c
        score = round(max(0.0, min(100.0, score)), 1)
        self._fatigue_buf.append(score)
        return score

    def get_avg_fatigue_score(self) -> float:
        return float(np.mean(self._fatigue_buf)) if self._fatigue_buf else 0.0

    def should_notify(self) -> bool:
        rate = self.get_blink_rate()
        if rate is None:
            return False
        now = time.time()
        if rate < self.low_rate_threshold:
            if (now - self._last_notif) >= self.notification_cooldown:
                self._last_notif = now
                logger.info(f"Low blink rate notification: {rate:.1f}/min")
                return True
        return False

    def get_session_duration(self) -> float:
        return time.time() - self._session_start

    def reset(self) -> None:
        self._blink_times.clear()
        self._blink_durs.clear()
        self._ear_buf.clear()
        self._fatigue_buf.clear()
        self.total_blinks = 0
        self._session_start = time.time()
        self._last_notif = 0.0
        logger.info("BlinkMonitor reset")

    # ------------------------------------------------------------------
    def _evict(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._blink_times and self._blink_times[0] < cutoff:
            self._blink_times.popleft()
        while self._blink_durs and self._blink_durs[0][0] < cutoff:
            self._blink_durs.popleft()
