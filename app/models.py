"""Database models and operations"""

import sqlite3
from contextlib import closing
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


def get_db_connection(db_path):
    """Get database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    """Initialize database with schema"""
    with closing(get_db_connection(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by_user_id INTEGER,
                is_closed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                can_drive INTEGER NOT NULL DEFAULT 0,
                seat_count INTEGER NOT NULL DEFAULT 0,
                comment TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES events(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

        columns = [row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()]
        if "is_closed" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN is_closed INTEGER NOT NULL DEFAULT 0")
        if "recruitment_deadline" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN recruitment_deadline TEXT")

        conn.commit()


# User operations
def get_user_by_id(db_path, user_id):
    """Get user by ID"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_username(db_path, username):
    """Get user by username"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def create_user(db_path, username, password):
    """Create a new user"""
    with closing(get_db_connection(db_path)) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()


# Event operations
def get_all_events(db_path):
    """Get all events ordered by date"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute(
            "SELECT * FROM events ORDER BY event_date ASC, id DESC"
        ).fetchall()


def get_event_by_id(db_path, event_id):
    """Get event by ID"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()


def create_event(db_path, title, event_date, summary, user_id, recruitment_deadline=None):
    """Create a new event"""
    with closing(get_db_connection(db_path)) as conn:
        conn.execute(
            "INSERT INTO events (title, event_date, summary, created_at, created_by_user_id, recruitment_deadline) VALUES (?, ?, ?, ?, ?, ?)",
            (title, event_date, summary, datetime.now().strftime("%Y-%m-%d %H:%M"), user_id, recruitment_deadline)
        )
        conn.commit()


def update_event(db_path, event_id, title, event_date, summary, recruitment_deadline=None):
    """Update event details"""
    with closing(get_db_connection(db_path)) as conn:
        conn.execute(
            "UPDATE events SET title = ?, event_date = ?, summary = ?, recruitment_deadline = ? WHERE id = ?",
            (title, event_date, summary, recruitment_deadline, event_id)
        )
        conn.commit()


def toggle_event_close(db_path, event_id):
    """Toggle event closed status"""
    with closing(get_db_connection(db_path)) as conn:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event:
            new_value = 0 if event["is_closed"] else 1
            conn.execute("UPDATE events SET is_closed = ? WHERE id = ?", (new_value, event_id))
            conn.commit()
            return new_value
    return None


def delete_event(db_path, event_id):
    """Delete event and its participants"""
    with closing(get_db_connection(db_path)) as conn:
        conn.execute("DELETE FROM participants WHERE event_id = ?", (event_id,))
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()


# Participant operations
def get_event_participants(db_path, event_id):
    """Get all participants for an event"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute(
            """
            SELECT p.*, u.username
            FROM participants p
            JOIN users u ON p.user_id = u.id
            WHERE p.event_id = ?
            ORDER BY
              CASE p.status WHEN '参加希望' THEN 0 WHEN '未定' THEN 1 ELSE 2 END,
              p.can_drive DESC,
              p.updated_at ASC,
              p.id ASC
            """,
            (event_id,)
        ).fetchall()


def get_user_participation(db_path, event_id, user_id):
    """Get user participation record for an event"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute(
            "SELECT * FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id)
        ).fetchone()


def create_or_update_participation(db_path, event_id, user_id, status, can_drive, seat_count, comment):
    """Create or update participant record"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    with closing(get_db_connection(db_path)) as conn:
        existing = conn.execute(
            "SELECT id FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id)
        ).fetchone()

        if can_drive == 0:
            seat_count = 0

        if existing:
            conn.execute(
                """
                UPDATE participants
                SET status = ?, can_drive = ?, seat_count = ?, comment = ?, updated_at = ?
                WHERE event_id = ? AND user_id = ?
                """,
                (status, can_drive, max(seat_count, 0), comment, now, event_id, user_id)
            )
        else:
            conn.execute(
                """
                INSERT INTO participants (event_id, user_id, status, can_drive, seat_count, comment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, user_id, status, can_drive, max(seat_count, 0), comment, now, now)
            )
        conn.commit()


def has_user_participated(db_path, event_id, user_id):
    """Check if user has already responded to an event"""
    if not user_id:
        return False
    with closing(get_db_connection(db_path)) as conn:
        result = conn.execute(
            "SELECT id FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id)
        ).fetchone()
    return result is not None


def get_user_ongoing_participated_events(db_path, user_id):
    """Get ongoing (recruiting) events that user wants to participate in"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute(
            """
            SELECT e.*, p.status, p.can_drive, p.seat_count, p.comment
            FROM events e
            JOIN participants p ON e.id = p.event_id
            WHERE p.user_id = ? AND e.is_closed = 0 AND p.status = '参加希望'
            ORDER BY e.event_date ASC, e.id DESC
            """,
            (user_id,)
        ).fetchall()


def get_user_past_participated_events(db_path, user_id):
    """Get past (closed) events that user participated in"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute(
            """
            SELECT e.*, p.status, p.can_drive, p.seat_count, p.comment
            FROM events e
            JOIN participants p ON e.id = p.event_id
            WHERE p.user_id = ? AND e.is_closed = 1
            ORDER BY e.event_date DESC, e.id DESC
            """,
            (user_id,)
        ).fetchall()


def get_user_created_events(db_path, user_id):
    """Get all events created by user, ordered by date (newest first)"""
    with closing(get_db_connection(db_path)) as conn:
        return conn.execute(
            """
            SELECT * FROM events
            WHERE created_by_user_id = ?
            ORDER BY event_date DESC, id DESC
            """,
            (user_id,)
        ).fetchall()
