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


def get_sessions_records(limit: int = 100) -> list[dict]:
    """Returns rows ordered newest first as dictionaries including ID."""
    with _conn() as con:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            """
            SELECT id, start_time, end_time, duration_secs, total_blinks,
                   avg_blink_rate, avg_fatigue_score, avg_blink_duration_ms, ear_threshold
            FROM sessions ORDER BY id DESC LIMIT ?
        """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]


def delete_session(session_id: int) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        con.commit()
        return cur.rowcount > 0


def clear_sessions() -> None:
    with _conn() as con:
        con.execute("DELETE FROM sessions")
        con.commit()


def get_database_summary() -> dict:
    with _conn() as con:
        cur = con.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                COALESCE(SUM(duration_secs), 0) as total_duration_secs,
                COALESCE(SUM(total_blinks), 0) as total_blinks,
                COALESCE(AVG(avg_blink_rate), 0) as overall_avg_blink_rate,
                COALESCE(AVG(avg_fatigue_score), 0) as overall_avg_fatigue_score
            FROM sessions
        """)
        row = cur.fetchone()
        return {
            "total_sessions": row[0] if row else 0,
            "total_duration_secs": round(row[1], 1) if row else 0,
            "total_blinks": row[2] if row else 0,
            "overall_avg_blink_rate": round(row[3], 1) if row else 0,
            "overall_avg_fatigue_score": round(row[4], 1) if row else 0,
        }

