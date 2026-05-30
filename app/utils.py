"""Utility functions"""

from contextlib import closing
import sqlite3


def current_user(db_path, session):
    """Get current logged-in user from session"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def event_stats(db_path, event_id):
    """Calculate event statistics"""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        participant_count = conn.execute(
            "SELECT COUNT(*) FROM participants WHERE event_id = ? AND status = '参加希望'",
            (event_id,)
        ).fetchone()[0]
        total_seats = conn.execute(
            "SELECT COALESCE(SUM(seat_count), 0) FROM participants WHERE event_id = ? AND can_drive = 1 AND status = '参加希望'",
            (event_id,)
        ).fetchone()[0]
        driver_count = conn.execute(
            "SELECT COUNT(*) FROM participants WHERE event_id = ? AND can_drive = 1 AND status = '参加希望'",
            (event_id,)
        ).fetchone()[0]
    
    return {
        "participant_count": participant_count,
        "total_seats": total_seats,
        "driver_count": driver_count,
    }
