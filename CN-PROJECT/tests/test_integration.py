import sys
import os
import socket
import base64
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSmtpIntegration(unittest.TestCase):
    """End-to-end SMTP conversation tests against a running server."""

    HOST = "127.0.0.1"
    PORT = 2525

    def _connect(self):
        """Create a socket connection to the SMTP server."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((self.HOST, self.PORT))
            return sock
        except ConnectionRefusedError:
            self.skipTest("SMTP server not running. Start with: python run_server.py")

    def _send(self, sock, command):
        """Send a command and return the response."""
        sock.sendall((command + "\r\n").encode())
        time.sleep(0.2)
        return sock.recv(4096).decode().strip()

    def _recv(self, sock):
        """Read response from server."""
        return sock.recv(4096).decode().strip()

    def test_01_server_greeting(self):
        """Server should send 220 greeting on connect."""
        sock = self._connect()
        greeting = self._recv(sock)
        self.assertTrue(greeting.startswith("220"), f"Expected 220, got: {greeting}")
        sock.close()

    def test_02_ehlo(self):
        """EHLO should return 250 with capabilities."""
        sock = self._connect()
        self._recv(sock) 
        response = self._send(sock, "EHLO testclient.local")
        self.assertIn("250", response)
        self.assertIn("AUTH", response)
        sock.close()

    def test_03_auth_login(self):
        """AUTH LOGIN should authenticate valid user."""
        sock = self._connect()
        self._recv(sock)
        self._send(sock, "EHLO testclient.local")

        response = self._send(sock, "AUTH LOGIN")
        self.assertTrue(response.startswith("334"))

        username_b64 = base64.b64encode(b"huzaifa@alpha.local").decode()
        response = self._send(sock, username_b64)
        self.assertTrue(response.startswith("334"))

        password_b64 = base64.b64encode(b"huzaifa123").decode()
        response = self._send(sock, password_b64)
        self.assertTrue(response.startswith("235"), f"Expected 235, got: {response}")

        sock.close()

    def test_04_full_email_flow(self):
        """Test complete email send flow: EHLO -> AUTH -> MAIL FROM -> RCPT TO -> DATA."""
        sock = self._connect()
        self._recv(sock)

        self._send(sock, "EHLO testclient.local")

        self._send(sock, "AUTH LOGIN")
        self._send(sock, base64.b64encode(b"huzaifa@alpha.local").decode())
        response = self._send(sock, base64.b64encode(b"huzaifa123").decode())
        self.assertTrue(response.startswith("235"))

        response = self._send(sock, "MAIL FROM:<huzaifa@alpha.local>")
        self.assertTrue(response.startswith("250"), f"MAIL FROM failed: {response}")

        response = self._send(sock, "RCPT TO:<ali@beta.local>")
        self.assertTrue(response.startswith("250"), f"RCPT TO failed: {response}")

        response = self._send(sock, "DATA")
        self.assertTrue(response.startswith("354"), f"DATA failed: {response}")

        lines = ["Subject: Integration Test", "", "This is a test email from the integration test suite.", "."]
        for line in lines:
            sock.sendall((line + "\r\n").encode())
        time.sleep(0.5)
        response = sock.recv(4096).decode().strip()
        self.assertIn("250", response, f"Message not accepted: {response}")

        response = self._send(sock, "QUIT")
        self.assertTrue(response.startswith("221"))

        sock.close()

    def test_05_invalid_recipient(self):
        """RCPT TO with unknown user should return 550."""
        sock = self._connect()
        self._recv(sock)
        self._send(sock, "EHLO testclient.local")

        self._send(sock, "AUTH LOGIN")
        self._send(sock, base64.b64encode(b"huzaifa@alpha.local").decode())
        self._send(sock, base64.b64encode(b"huzaifa123").decode())

        self._send(sock, "MAIL FROM:<huzaifa@alpha.local>")
        response = self._send(sock, "RCPT TO:<nonexistent@alpha.local>")
        self.assertTrue(response.startswith("550"), f"Expected 550, got: {response}")

        sock.close()

    def test_06_wrong_auth(self):
        """AUTH with wrong password should return 535."""
        sock = self._connect()
        self._recv(sock)
        self._send(sock, "EHLO testclient.local")

        self._send(sock, "AUTH LOGIN")
        self._send(sock, base64.b64encode(b"huzaifa@alpha.local").decode())
        response = self._send(sock, base64.b64encode(b"wrongpassword").decode())
        self.assertTrue(response.startswith("535"), f"Expected 535, got: {response}")

        sock.close()

    def test_07_noop(self):
        """NOOP should return 250."""
        sock = self._connect()
        self._recv(sock)
        response = self._send(sock, "NOOP")
        self.assertTrue(response.startswith("250"))
        sock.close()

    def test_08_multiple_clients(self):
        """Test that multiple clients can connect simultaneously."""
        sockets = []
        try:
            for i in range(3):
                sock = self._connect()
                greeting = self._recv(sock)
                self.assertTrue(greeting.startswith("220"))
                sockets.append(sock)

            for sock in sockets:
                response = self._send(sock, "EHLO multiclient.local")
                self.assertIn("250", response)

        finally:
            for sock in sockets:
                try:
                    sock.close()
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
