from datetime import datetime
from utils.logger import storage_logger as logger


class MailStore:
    """Persistent email storage backed by SQLite."""

    def __init__(self, db_manager):
        self.db = db_manager

    def store_message(self, sender, recipient, subject, body):
        """Save a delivered email to the messages table."""
        try:
            msg_id = self.db.execute(
                """INSERT INTO messages (sender, recipient, subject, body, timestamp, is_read, status)
                   VALUES (?, ?, ?, ?, ?, 0, 'delivered')""",
                (sender.lower(), recipient.lower(), subject, body,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            logger.info(f"Message stored: {sender} -> {recipient} (id={msg_id})")
            return msg_id
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            return None

    def get_inbox(self, email):
        """Get all messages received by this user, newest first."""
        rows = self.db.fetch_all(
            """SELECT id, sender, recipient, subject, body, timestamp, is_read
               FROM messages WHERE recipient = ?
               ORDER BY timestamp DESC""",
            (email.lower(),)
        )
        return [dict(row) for row in rows] if rows else []

    def get_sent(self, email):
        """Get all messages sent by this user, newest first."""
        rows = self.db.fetch_all(
            """SELECT id, sender, recipient, subject, body, timestamp
               FROM messages WHERE sender = ?
               ORDER BY timestamp DESC""",
            (email.lower(),)
        )
        return [dict(row) for row in rows] if rows else []

    def get_message(self, message_id):
        """Get a single message by its ID."""
        row = self.db.fetch_one(
            "SELECT * FROM messages WHERE id = ?", (message_id,)
        )
        return dict(row) if row else None

    def mark_as_read(self, message_id):
        """Mark a message as read."""
        self.db.execute(
            "UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,)
        )

    def get_unread_count(self, email):
        """Count unread messages for a user."""
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM messages WHERE recipient = ? AND is_read = 0",
            (email.lower(),)
        )
        return row["count"] if row else 0

    def delete_message(self, message_id):
        """Delete a message by ID."""
        self.db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        logger.info(f"Message deleted: id={message_id}")
