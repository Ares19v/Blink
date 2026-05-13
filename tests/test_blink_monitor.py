"""
test_blink_monitor.py
pytest unit tests for BlinkMonitor logic.
No camera or GUI required — pure Python.
"""
import time
import pytest
from core.blink_monitor import BlinkMonitor


@pytest.fixture
def monitor():
    return BlinkMonitor(window_seconds=60, low_rate_threshold=12.0, notification_cooldown=5.0)


def test_initial_state(monitor):
    assert monitor.total_blinks == 0
    assert monitor.get_blink_rate() is None  # <10 s of data


def test_register_blink_increments_count(monitor):
    monitor.register_blink(150.0)
    monitor.register_blink(120.0)
    assert monitor.total_blinks == 2


def test_blink_rate_calculation(monitor):
    # Simulate 15 blinks spread over ~10 s
    monitor._session_start = time.time() - 15
    for _ in range(15):
        monitor._blink_times.append(time.time())
    rate = monitor.get_blink_rate()
    assert rate is not None
    assert 50 < rate < 70  # ~15 blinks in 15 s = 60/min


def test_should_notify_when_rate_low(monitor):
    monitor._session_start = time.time() - 30
    # Only 2 blinks → ~4/min < 12 threshold
    monitor.register_blink(100.0)
    monitor.register_blink(100.0)
    assert monitor.should_notify() is True


def test_should_not_notify_twice_within_cooldown(monitor):
    monitor._session_start = time.time() - 30
    monitor.register_blink(100.0)
    monitor.register_blink(100.0)
    assert monitor.should_notify() is True
    # Second call within cooldown
    assert monitor.should_notify() is False


def test_should_not_notify_when_rate_healthy(monitor):
    monitor._session_start = time.time() - 15
    for _ in range(20):
        monitor.register_blink(150.0)
    assert monitor.should_notify() is False


def test_avg_blink_duration(monitor):
    monitor.register_blink(100.0)
    monitor.register_blink(200.0)
    avg = monitor.get_avg_blink_duration_ms()
    assert abs(avg - 150.0) < 0.01


def test_fatigue_score_range(monitor):
    monitor._session_start = time.time() - 30
    for _ in range(6):
        monitor.register_blink(150.0)
    monitor.register_ear(0.27)
    score = monitor.get_fatigue_score()
    assert score is None or 0.0 <= score <= 100.0


def test_reset_clears_state(monitor):
    monitor.register_blink(100.0)
    monitor.reset()
    assert monitor.total_blinks == 0
    assert monitor.get_blink_rate() is None
