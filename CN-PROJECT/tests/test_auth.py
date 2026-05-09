import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.db_manager import DatabaseManager
from core.auth_manager import AuthManager


class TestAuthentication(unittest.TestCase):
    """Test user authentication and management."""

    def setUp(self):
        self.db = DatabaseManager("data/test_auth.db")
        self.auth = AuthManager(self.db)

    def tearDown(self):
        try:
            os.remove("data/test_auth.db")
        except FileNotFoundError:
            pass

    def test_register_user(self):
        """Should register a new user successfully."""
        result = self.auth.register_user("test@alpha.local", "password123")
        self.assertTrue(result)

    def test_register_duplicate(self):
        """Should fail to register duplicate email."""
        self.auth.register_user("test@alpha.local", "password123")
        result = self.auth.register_user("test@alpha.local", "password456")
        self.assertFalse(result)

    def test_authenticate_valid(self):
        """Should authenticate with correct credentials."""
        self.auth.register_user("test@alpha.local", "password123")
        result = self.auth.authenticate("test@alpha.local", "password123")
        self.assertTrue(result)

    def test_authenticate_wrong_password(self):
        """Should reject wrong password."""
        self.auth.register_user("test@alpha.local", "password123")
        result = self.auth.authenticate("test@alpha.local", "wrongpassword")
        self.assertFalse(result)

    def test_authenticate_nonexistent(self):
        """Should reject non-existent user."""
        result = self.auth.authenticate("nobody@alpha.local", "password123")
        self.assertFalse(result)

    def test_user_exists(self):
        """Should correctly check if user exists."""
        self.auth.register_user("test@alpha.local", "password123")
        self.assertTrue(self.auth.user_exists("test@alpha.local"))
        self.assertFalse(self.auth.user_exists("nobody@alpha.local"))

    def test_get_user(self):
        """Should return user details."""
        self.auth.register_user("huzaifa@alpha.local", "huzaifa123", "Huzaifa", "alpha.local")
        user = self.auth.get_user("huzaifa@alpha.local")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "Huzaifa")
        self.assertEqual(user["domain"], "alpha.local")

    def test_password_hashing(self):
        """Password should be hashed, not stored in plaintext."""
        self.auth.register_user("test@alpha.local", "password123")
        user = self.auth.get_user("test@alpha.local")
        self.assertNotEqual(user["password_hash"], "password123")

    def test_case_insensitive_email(self):
        """Email lookup should be case-insensitive."""
        self.auth.register_user("Test@Alpha.Local", "password123")
        self.assertTrue(self.auth.user_exists("test@alpha.local"))

    def test_get_domain_users(self):
        """Should return users filtered by domain."""
        self.auth.register_user("user1@alpha.local", "pass1")
        self.auth.register_user("user2@alpha.local", "pass2")
        self.auth.register_user("user3@beta.local", "pass3")

        alpha_users = self.auth.get_domain_users("alpha.local")
        self.assertEqual(len(alpha_users), 2)


if __name__ == "__main__":
    unittest.main()
