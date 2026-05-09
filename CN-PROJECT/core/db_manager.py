import sqlite3
import os
import threading
from utils.logger import storage_logger as logger


class DatabaseManager:
    """Manages SQLite database connections and schema."""

    def __init__(self, db_path="data/smtp_server.db"):
        self.db_path = db_path
        self._lock = threading.Lock()

        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

        self._init_schema()

    def get_connection(self):
        """Get a new database connection (thread-safe)."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  
        conn.execute("PRAGMA journal_mode=WAL") 
        return conn

    def _init_schema(self):
        """Create tables if they don't already exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT DEFAULT '',
                    body TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'delivered'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mail_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT DEFAULT '',
                    body TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_retry TIMESTAMP,
                    last_error TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_recipient
                ON messages(recipient)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_sender
                ON messages(sender)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_status
                ON mail_queue(status)
            """)

            conn.commit()
            logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
        finally:
            conn.close()

    def execute(self, query, params=None):
        """Execute a query with thread safety. Returns lastrowid for INSERTs."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.lastrowid
            except sqlite3.Error as e:
                logger.error(f"Database error: {e} | Query: {query}")
                conn.rollback()
                raise
            finally:
                conn.close()

    def fetch_one(self, query, params=None):
        """Fetch a single row."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchone()
            finally:
                conn.close()

    def fetch_all(self, query, params=None):
        """Fetch all matching rows."""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            finally:
                conn.close()
