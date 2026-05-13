"""
database.py
SQLite session history — stores one row per monitoring session.
"""

import sqlite3
import os
from datetime import datetime

_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "blink_history.db"
)


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(_DB_PATH)


def init_db() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time           TEXT NOT NULL,
                end_time             TEXT NOT NULL,
                duration_secs        REAL,
                total_blinks         INTEGER,
                avg_blink_rate       REAL,
                avg_fatigue_score    REAL,
                avg_blink_duration_ms REAL,
                ear_threshold        REAL
            )
        """)
        con.commit()


def save_session(
    start_time: datetime,
    end_time: datetime,
    duration_secs: float,
    total_blinks: int,
    avg_blink_rate: float,
    avg_fatigue_score: float,
    avg_blink_duration_ms: float,
    ear_threshold: float,
) -> None:
    with _conn() as con:
        con.execute(
            """
            INSERT INTO sessions
              (start_time, end_time, duration_secs, total_blinks,
               avg_blink_rate, avg_fatigue_score, avg_blink_duration_ms, ear_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                start_time.isoformat(),
                end_time.isoformat(),
                duration_secs,
                total_blinks,
                avg_blink_rate,
                avg_fatigue_score,
                avg_blink_duration_ms,
                ear_threshold,
            ),
        )
        con.commit()


def get_sessions(limit: int = 30) -> list[tuple]:
    """Returns rows ordered newest first."""
    with _conn() as con:
        cur = con.execute(
            """
            SELECT start_time, end_time, duration_secs, total_blinks,
                   avg_blink_rate, avg_fatigue_score, avg_blink_duration_ms
            FROM sessions ORDER BY start_time DESC LIMIT ?
        """,
            (limit,),
        )
        return cur.fetchall()
