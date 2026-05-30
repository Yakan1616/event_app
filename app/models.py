"""Database models and operations"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

def get_db_url():
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL", "sqlite:///circle_events.db")

def get_db_connection(db_url=None):
    """Get database connection - supports both SQLite and PostgreSQL"""
    if db_url is None:
        db_url = get_db_url()
    
    if db_url.startswith("sqlite://"):
        # SQLite mode for local development
        import sqlite3
        db_path = db_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # PostgreSQL mode - import only when needed
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn


def init_db(db_url=None):
    """Initialize database with schema"""
    if db_url is None:
        db_url = get_db_url()
    
    if db_url.startswith("sqlite://"):
        # SQLite initialization
        import sqlite3
        from contextlib import closing
        db_path = db_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        with closing(conn) as conn:
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
                    recruitment_deadline TEXT,
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
            conn.commit()
    else:
        # PostgreSQL initialization
        conn = get_db_connection(db_url)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        event_date TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        created_by_user_id INTEGER,
                        is_closed INTEGER NOT NULL DEFAULT 0,
                        recruitment_deadline TEXT,
                        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS participants (
                        id SERIAL PRIMARY KEY,
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
                """)
                
                conn.commit()
        finally:
            conn.close()



# User operations
def get_user_by_id(db_url, user_id):
    """Get user by ID"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone()
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                return cur.fetchone()
    finally:
        conn.close()


def get_user_by_username(db_url, username):
    """Get user by username"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            return cursor.fetchone()
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                return cur.fetchone()
    finally:
        conn.close()


def create_user(db_url, username, password):
    """Create a new user"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s)",
                    (username, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
    finally:
        conn.close()


# Event operations
def get_all_events(db_url):
    """Get all events ordered by date"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY event_date ASC, id DESC")
            return cursor.fetchall()
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM events ORDER BY event_date ASC, id DESC")
                return cur.fetchall()
    finally:
        conn.close()


def get_event_by_id(db_url, event_id):
    """Get event by ID"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            return cursor.fetchone()
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
                return cur.fetchone()
    finally:
        conn.close()


def create_event(db_url, title, event_date, summary, user_id, recruitment_deadline=None):
    """Create a new event"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (title, event_date, summary, created_at, created_by_user_id, recruitment_deadline) VALUES (?, ?, ?, ?, ?, ?)",
                (title, event_date, summary, datetime.now().strftime("%Y-%m-%d %H:%M"), user_id, recruitment_deadline)
            )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO events (title, event_date, summary, created_at, created_by_user_id, recruitment_deadline) VALUES (%s, %s, %s, %s, %s, %s)",
                    (title, event_date, summary, datetime.now().strftime("%Y-%m-%d %H:%M"), user_id, recruitment_deadline)
                )
                conn.commit()
    finally:
        conn.close()


def update_event(db_url, event_id, title, event_date, summary, recruitment_deadline=None):
    """Update event details"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE events SET title = ?, event_date = ?, summary = ?, recruitment_deadline = ? WHERE id = ?",
                (title, event_date, summary, recruitment_deadline, event_id)
            )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE events SET title = %s, event_date = %s, summary = %s, recruitment_deadline = %s WHERE id = %s",
                    (title, event_date, summary, recruitment_deadline, event_id)
                )
                conn.commit()
    finally:
        conn.close()


def toggle_event_close(db_url, event_id):
    """Toggle event closed status"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event = cursor.fetchone()
            if event:
                new_value = 0 if event["is_closed"] else 1
                cursor.execute("UPDATE events SET is_closed = ? WHERE id = ?", (new_value, event_id))
                conn.commit()
                return new_value
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM events WHERE id = %s", (event_id,))
                event = cur.fetchone()
                if event:
                    new_value = 0 if event["is_closed"] else 1
                    cur.execute("UPDATE events SET is_closed = %s WHERE id = %s", (new_value, event_id))
                    conn.commit()
                    return new_value
    finally:
        conn.close()
    return None


def delete_event(db_url, event_id):
    """Delete event and its participants"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM participants WHERE event_id = ?", (event_id,))
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM participants WHERE event_id = %s", (event_id,))
                cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
                conn.commit()
    finally:
        conn.close()


# Participant operations
def get_event_participants(db_url, event_id):
    """Get all participants for an event"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
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
            )
            return cursor.fetchall()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT p.*, u.username
                    FROM participants p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.event_id = %s
                    ORDER BY
                      CASE p.status WHEN '参加希望' THEN 0 WHEN '未定' THEN 1 ELSE 2 END,
                      p.can_drive DESC,
                      p.updated_at ASC,
                      p.id ASC
                    """,
                    (event_id,)
                )
                return cur.fetchall()
    finally:
        conn.close()


def get_user_participation(db_url, event_id, user_id):
    """Get user participation record for an event"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM participants WHERE event_id = ? AND user_id = ?",
                (event_id, user_id)
            )
            return cursor.fetchone()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM participants WHERE event_id = %s AND user_id = %s",
                    (event_id, user_id)
                )
                return cur.fetchone()
    finally:
        conn.close()


def create_or_update_participation(db_url, event_id, user_id, status, can_drive, seat_count, comment):
    """Create or update participant record"""
    if db_url is None:
        db_url = get_db_url()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM participants WHERE event_id = ? AND user_id = ?",
                (event_id, user_id)
            )
            existing = cursor.fetchone()

            if can_drive == 0:
                seat_count = 0

            if existing:
                cursor.execute(
                    """
                    UPDATE participants
                    SET status = ?, can_drive = ?, seat_count = ?, comment = ?, updated_at = ?
                    WHERE event_id = ? AND user_id = ?
                    """,
                    (status, can_drive, max(seat_count, 0), comment, now, event_id, user_id)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO participants (event_id, user_id, status, can_drive, seat_count, comment, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event_id, user_id, status, can_drive, max(seat_count, 0), comment, now, now)
                )
            conn.commit()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM participants WHERE event_id = %s AND user_id = %s",
                    (event_id, user_id)
                )
                existing = cur.fetchone()

                if can_drive == 0:
                    seat_count = 0

                if existing:
                    cur.execute(
                        """
                        UPDATE participants
                        SET status = %s, can_drive = %s, seat_count = %s, comment = %s, updated_at = %s
                        WHERE event_id = %s AND user_id = %s
                        """,
                        (status, can_drive, max(seat_count, 0), comment, now, event_id, user_id)
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO participants (event_id, user_id, status, can_drive, seat_count, comment, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (event_id, user_id, status, can_drive, max(seat_count, 0), comment, now, now)
                    )
                conn.commit()
    finally:
        conn.close()


def has_user_participated(db_url, event_id, user_id):
    """Check if user has already responded to an event"""
    if not user_id:
        return False
    
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM participants WHERE event_id = ? AND user_id = ?",
                (event_id, user_id)
            )
            result = cursor.fetchone()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM participants WHERE event_id = %s AND user_id = %s",
                    (event_id, user_id)
                )
                result = cur.fetchone()
        return result is not None
    finally:
        conn.close()


def get_user_ongoing_participated_events(db_url, user_id):
    """Get ongoing (recruiting) events that user wants to participate in"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, p.status, p.can_drive, p.seat_count, p.comment
                FROM events e
                JOIN participants p ON e.id = p.event_id
                WHERE p.user_id = ? AND e.is_closed = 0 AND p.status = '参加希望'
                ORDER BY e.event_date ASC, e.id DESC
                """,
                (user_id,)
            )
            return cursor.fetchall()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.*, p.status, p.can_drive, p.seat_count, p.comment
                    FROM events e
                    JOIN participants p ON e.id = p.event_id
                    WHERE p.user_id = %s AND e.is_closed = 0 AND p.status = '参加希望'
                    ORDER BY e.event_date ASC, e.id DESC
                    """,
                    (user_id,)
                )
                return cur.fetchall()
    finally:
        conn.close()


def get_user_past_participated_events(db_url, user_id):
    """Get past (closed) events that user participated in"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, p.status, p.can_drive, p.seat_count, p.comment
                FROM events e
                JOIN participants p ON e.id = p.event_id
                WHERE p.user_id = ? AND e.is_closed = 1
                ORDER BY e.event_date DESC, e.id DESC
                """,
                (user_id,)
            )
            return cursor.fetchall()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.*, p.status, p.can_drive, p.seat_count, p.comment
                    FROM events e
                    JOIN participants p ON e.id = p.event_id
                    WHERE p.user_id = %s AND e.is_closed = 1
                    ORDER BY e.event_date DESC, e.id DESC
                    """,
                    (user_id,)
                )
                return cur.fetchall()
    finally:
        conn.close()


def get_user_created_events(db_url, user_id):
    """Get all events created by user, ordered by date (newest first)"""
    if db_url is None:
        db_url = get_db_url()
    conn = get_db_connection(db_url)
    try:
        if db_url.startswith("sqlite://"):
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM events
                WHERE created_by_user_id = ?
                ORDER BY event_date DESC, id DESC
                """,
                (user_id,)
            )
            return cursor.fetchall()
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM events
                    WHERE created_by_user_id = %s
                    ORDER BY event_date DESC, id DESC
                    """,
                    (user_id,)
                )
                return cur.fetchall()
    finally:
        conn.close()
