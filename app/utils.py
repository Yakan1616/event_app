"""Utility functions"""

import sqlite3
import app.models as models


def current_user(db_url, session):
    """Get current logged-in user from session"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return models.get_user_by_id(db_url, user_id)


def event_stats(db_url, event_id):
    """Calculate event statistics"""
    conn = models.get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            participant_count = cursor.execute(
                "SELECT COUNT(*) FROM participants WHERE event_id = ? AND status = '参加希望'",
                (event_id,)
            ).fetchone()[0]
            total_seats = cursor.execute(
                "SELECT COALESCE(SUM(seat_count), 0) FROM participants WHERE event_id = ? AND can_drive = 1 AND status = '参加希望'",
                (event_id,)
            ).fetchone()[0]
            driver_count = cursor.execute(
                "SELECT COUNT(*) FROM participants WHERE event_id = ? AND can_drive = 1 AND status = '参加希望'",
                (event_id,)
            ).fetchone()[0]
        else:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as count FROM participants WHERE event_id = %s AND status = '参加希望'",
                (event_id,)
            )
            participant_count = cur.fetchone()["count"]
            cur.execute(
                "SELECT COALESCE(SUM(seat_count), 0) as total FROM participants WHERE event_id = %s AND can_drive = 1 AND status = '参加希望'",
                (event_id,)
            )
            total_seats = cur.fetchone()["total"]
            cur.execute(
                "SELECT COUNT(*) as count FROM participants WHERE event_id = %s AND can_drive = 1 AND status = '参加希望'",
                (event_id,)
            )
            driver_count = cur.fetchone()["count"]
            cur.close()
    finally:
        conn.close()
    
    # Calculate available seats (total seats - current participants)
    available_seats = max(0, total_seats - participant_count)
    
    return {
        "participant_count": participant_count,
        "total_seats": total_seats,
        "available_seats": available_seats,
        "driver_count": driver_count,
    }
