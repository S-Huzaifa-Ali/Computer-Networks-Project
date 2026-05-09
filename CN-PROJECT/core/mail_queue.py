import threading
import time
from datetime import datetime, timedelta
from utils.logger import queue_logger as logger


class MailQueue:
    """Thread-safe mail queue with background delivery worker."""

    def __init__(self, db_manager, mail_store, auth_manager, config=None):
        self.db = db_manager
        self.mail_store = mail_store
        self.auth_manager = auth_manager

        queue_config = config.get("queue", {}) if config else {}
        self.max_retries = queue_config.get("max_retries", 3)
        self.retry_delay = queue_config.get("retry_delay_seconds", 10)
        self.check_interval = queue_config.get("worker_interval", 3)

        self._running = False
        self._worker_thread = None

    def enqueue(self, sender, recipient, subject, body):
        """Add a message to the outgoing queue."""
        try:
            queue_id = self.db.execute(
                """INSERT INTO mail_queue
                   (sender, recipient, subject, body, status, attempts, max_retries, created_at)
                   VALUES (?, ?, ?, ?, 'pending', 0, ?, ?)""",
                (sender, recipient, subject, body, self.max_retries,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            logger.info(f"Message queued: {sender} -> {recipient} (queue_id={queue_id})")
            return queue_id
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return None

    def start_worker(self):
        """Start the background delivery worker thread."""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(
            target=self._delivery_loop, daemon=True, name="QueueWorker"
        )
        self._worker_thread.start()
        logger.info("Mail queue delivery worker started")

    def stop_worker(self):
        """Stop the delivery worker."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("Mail queue delivery worker stopped")

    def _delivery_loop(self):
        """Main loop for the delivery worker - runs in background thread."""
        while self._running:
            try:
                self._process_pending()
            except Exception as e:
                logger.error(f"Delivery worker error: {e}")
            time.sleep(self.check_interval)

    def _process_pending(self):
        """Try to deliver all pending messages in the queue."""
        pending = self.db.fetch_all(
            """SELECT * FROM mail_queue
               WHERE status = 'pending'
               ORDER BY created_at ASC"""
        )

        if not pending:
            return

        for item in pending:
            self._deliver_message(dict(item))

    def _deliver_message(self, queue_item):
        queue_id = queue_item["id"]
        sender = queue_item["sender"]
        recipient = queue_item["recipient"]
        attempts = queue_item["attempts"] + 1

        logger.info(f"Delivering queue item {queue_id}: {sender} -> {recipient} (attempt {attempts})")

        if not self.auth_manager.user_exists(recipient):
            self.db.execute(
                """UPDATE mail_queue SET status = 'failed',
                   last_error = 'Recipient not found', attempts = ?
                   WHERE id = ?""",
                (attempts, queue_id)
            )
            logger.warning(f"Delivery failed - recipient not found: {recipient}")
            return

        try:
            self.mail_store.store_message(
                sender, recipient,
                queue_item["subject"], queue_item["body"]
            )

            self.db.execute(
                "UPDATE mail_queue SET status = 'delivered', attempts = ? WHERE id = ?",
                (attempts, queue_id)
            )
            logger.info(f"Message delivered successfully: {sender} -> {recipient}")

        except Exception as e:
            if attempts >= self.max_retries:
                self.db.execute(
                    """UPDATE mail_queue SET status = 'failed',
                       attempts = ?, last_error = ? WHERE id = ?""",
                    (attempts, str(e), queue_id)
                )
                logger.error(f"Delivery permanently failed after {attempts} attempts: {e}")
            else:
                next_retry = datetime.now() + timedelta(seconds=self.retry_delay * attempts)
                self.db.execute(
                    """UPDATE mail_queue SET attempts = ?,
                       next_retry = ?, last_error = ? WHERE id = ?""",
                    (attempts, next_retry.strftime("%Y-%m-%d %H:%M:%S"),
                     str(e), queue_id)
                )
                logger.warning(f"Delivery attempt {attempts} failed, will retry: {e}")

    def get_queue_status(self):
        """Get counts of messages in each queue state."""
        result = {"pending": 0, "delivered": 0, "failed": 0}
        for status in result:
            row = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM mail_queue WHERE status = ?",
                (status,)
            )
            if row:
                result[status] = row["count"]
        return result

    def get_pending_items(self):
        """Get all pending queue items for monitoring."""
        rows = self.db.fetch_all(
            """SELECT * FROM mail_queue WHERE status = 'pending'
               ORDER BY created_at ASC"""
        )
        return [dict(row) for row in rows] if rows else []

    def get_recent_items(self, limit=20):
        """Get recent queue items regardless of status."""
        rows = self.db.fetch_all(
            """SELECT * FROM mail_queue ORDER BY created_at DESC LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in rows] if rows else []
