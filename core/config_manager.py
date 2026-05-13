"""
config_manager.py
Loads and saves user configuration to config.json in the project root.
"""

import json
import os

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
)

DEFAULT_CONFIG: dict = {
    "camera_index": 0,
    "blink_rate_threshold": 12.0,
    "notification_cooldown": 90,
    "ear_threshold": 0.21,
    "twenty_twenty_twenty_enabled": True,
    "twenty_twenty_twenty_interval_sec": 1200,
    "sound_enabled": True,
    "calibrated": False,
}


def load_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
