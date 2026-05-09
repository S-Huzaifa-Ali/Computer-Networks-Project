import hashlib
import os
from utils.logger import auth_logger as logger


class AuthManager:
    """Manages user authentication and registration."""

    def __init__(self, db_manager):
        self.db = db_manager

    def _generate_salt(self):
        """Generate a random 16-byte salt as hex string."""
        return os.urandom(16).hex()

    def _hash_password(self, password, salt):
        """Hash password with salt using SHA-256."""
        salted = (salt + password).encode("utf-8")
        return hashlib.sha256(salted).hexdigest()

    def register_user(self, email, password, username=None, domain=None):
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE email = ?", (email.lower(),)
        )
        if existing:
            logger.warning(f"Registration failed - email already exists: {email}")
            return False

        if not username:
            username = email.split("@")[0]
        if not domain:
            domain = email.split("@")[1]

        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)

        try:
            self.db.execute(
                "INSERT INTO users (email, username, domain, password_hash, salt) VALUES (?, ?, ?, ?, ?)",
                (email.lower(), username, domain.lower(), password_hash, salt)
            )
            logger.info(f"User registered successfully: {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to register user {email}: {e}")
            return False

    def authenticate(self, email, password):
        """Verify user credentials."""
        user = self.db.fetch_one(
            "SELECT password_hash, salt FROM users WHERE email = ?",
            (email.lower(),)
        )

        if not user:
            logger.warning(f"Auth failed - user not found: {email}")
            return False

        stored_hash = user["password_hash"]
        salt = user["salt"]
        computed_hash = self._hash_password(password, salt)

        if computed_hash == stored_hash:
            logger.info(f"Authentication successful: {email}")
            return True
        else:
            logger.warning(f"Auth failed - wrong password: {email}")
            return False

    def get_user(self, email):
        """Look up a user by email. Returns the row or None."""
        return self.db.fetch_one(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        )

    def user_exists(self, email):
        """Quick check if an email is registered."""
        user = self.db.fetch_one(
            "SELECT id FROM users WHERE email = ?", (email.lower(),)
        )
        return user is not None

    def get_all_users(self):
        """Get list of all registered users."""
        return self.db.fetch_all("SELECT email, username, domain FROM users ORDER BY domain, username")

    def get_domain_users(self, domain):
        """Get all users belonging to a specific domain."""
        return self.db.fetch_all(
            "SELECT email, username FROM users WHERE domain = ? ORDER BY username",
            (domain.lower(),)
        )
