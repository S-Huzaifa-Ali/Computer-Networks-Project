import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.db_manager import DatabaseManager
from core.auth_manager import AuthManager
from core.domain_manager import DomainManager
from core.mail_store import MailStore
from core.mail_queue import MailQueue
from server.smtp_commands import SmtpCommandHandler


class TestSmtpCommands(unittest.TestCase):
    """Test SMTP command handling and state machine."""

    def setUp(self):
        """Set up a fresh handler with test database for each test."""
        self.db = DatabaseManager("data/test_smtp.db")
        self.auth = AuthManager(self.db)
        self.domain = DomainManager("config.json")
        self.store = MailStore(self.db)
        self.queue = MailQueue(self.db, self.store, self.auth)

        self.auth.register_user("testuser@alpha.local", "test123")

        self.handler = SmtpCommandHandler(self.auth, self.domain, self.queue)

    def tearDown(self):
        """Clean up test database."""
        try:
            os.remove("data/test_smtp.db")
        except FileNotFoundError:
            pass

    def test_greeting(self):
        """Server should send 220 greeting on connect."""
        greeting = self.handler.get_greeting()
        self.assertTrue(greeting.startswith("220"))

    def test_helo(self):
        """HELO should return 250 and set state to GREETED."""
        response = self.handler.process_command("HELO client.local")
        self.assertTrue(response.startswith("250"))
        self.assertEqual(self.handler.state, "GREETED")

    def test_ehlo(self):
        """EHLO should return 250 with capabilities."""
        response = self.handler.process_command("EHLO client.local")
        self.assertIn("250", response)
        self.assertIn("AUTH", response)
        self.assertEqual(self.handler.state, "GREETED")

    def test_helo_no_arg(self):
        """HELO without domain should return 501."""
        response = self.handler.process_command("HELO")
        self.assertTrue(response.startswith("501"))

    def test_noop(self):
        """NOOP should always return 250."""
        response = self.handler.process_command("NOOP")
        self.assertTrue(response.startswith("250"))

    def test_quit(self):
        """QUIT should return 221."""
        response = self.handler.process_command("QUIT")
        self.assertTrue(response.startswith("221"))

    def test_rset(self):
        """RSET should return 250 and reset session."""
        self.handler.process_command("EHLO client.local")
        response = self.handler.process_command("RSET")
        self.assertTrue(response.startswith("250"))

    def test_unknown_command(self):
        """Unknown commands should return 500."""
        response = self.handler.process_command("INVALID")
        self.assertTrue(response.startswith("500"))

    def test_mail_from_before_auth(self):
        """MAIL FROM before authentication should return 503."""
        self.handler.process_command("EHLO client.local")
        response = self.handler.process_command("MAIL FROM:<testuser@alpha.local>")
        self.assertTrue(response.startswith("503"))

    def test_rcpt_to_before_mail_from(self):
        """RCPT TO before MAIL FROM should return 503."""
        self.handler.process_command("EHLO client.local")
        response = self.handler.process_command("RCPT TO:<testuser@alpha.local>")
        self.assertTrue(response.startswith("503"))

    def test_data_before_rcpt(self):
        """DATA before RCPT TO should return 503."""
        self.handler.process_command("EHLO client.local")
        response = self.handler.process_command("DATA")
        self.assertTrue(response.startswith("503"))

    def test_invalid_email_format(self):
        """MAIL FROM with invalid email should return 501."""
        self.handler.process_command("EHLO client.local")
        self.handler.state = "AUTHENTICATED"
        self.handler.authenticated_user = "testuser@alpha.local"
        response = self.handler.process_command("MAIL FROM:<invalid>")
        self.assertTrue(response.startswith("501"))

    def test_unknown_recipient(self):
        """RCPT TO with non-existent user should return 550."""
        self.handler.process_command("EHLO client.local")
        self.handler.state = "AUTHENTICATED"
        self.handler.authenticated_user = "testuser@alpha.local"
        self.handler.process_command("MAIL FROM:<testuser@alpha.local>")
        response = self.handler.process_command("RCPT TO:<nobody@alpha.local>")
        self.assertTrue(response.startswith("550"))


if __name__ == "__main__":
    unittest.main()
