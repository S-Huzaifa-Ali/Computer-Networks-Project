import socket
import base64
from utils.logger import server_logger as logger


class SmtpClient:
    """Client for sending emails via our SMTP server."""

    def __init__(self, host="127.0.0.1", port=2525, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False

    def connect(self):
        """Connect to the SMTP server and read the 220 greeting."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))

            # read the 220 greeting
            response = self._recv()
            if not response.startswith("220"):
                raise ConnectionError(f"Server did not send 220 greeting: {response}")

            self.connected = True
            logger.info(f"Connected to SMTP server at {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"SMTP connect failed: {e}")
            self.connected = False
            return False

    def ehlo(self, domain="client.local"):
        """Send EHLO command."""
        response = self._send_command(f"EHLO {domain}")
        if not response or not response.startswith("250"):
            raise Exception(f"EHLO failed: {response}")
        return response

    def authenticate(self, email, password):
        """Perform AUTH LOGIN handshake."""
        response = self._send_command("AUTH LOGIN")
        if not response or not response.startswith("334"):
            return False, f"AUTH LOGIN rejected: {response}"

        username_b64 = base64.b64encode(email.encode()).decode()
        response = self._send_command(username_b64)
        if not response or not response.startswith("334"):
            return False, f"Username rejected: {response}"

        password_b64 = base64.b64encode(password.encode()).decode()
        response = self._send_command(password_b64)
        if response and response.startswith("235"):
            return True, "Authentication successful"
        else:
            return False, f"Authentication failed: {response}"

    def send_mail(self, sender, recipient, subject, body):
        try:
            response = self._send_command(f"MAIL FROM:<{sender}>")
            if not response or not response.startswith("250"):
                return False, f"MAIL FROM rejected: {response}"

            response = self._send_command(f"RCPT TO:<{recipient}>")
            if not response or not response.startswith("250"):
                return False, f"RCPT TO rejected: {response}"

            response = self._send_command("DATA")
            if not response or not response.startswith("354"):
                return False, f"DATA rejected: {response}"

            message_lines = [
                f"From: {sender}",
                f"To: {recipient}",
                f"Subject: {subject}",
                "", 
                body,
                "." 
            ]
            message = "\r\n".join(message_lines) + "\r\n"
            self.socket.sendall(message.encode("utf-8"))

            response = self._recv()
            if response and response.startswith("250"):
                logger.info(f"Mail sent: {sender} -> {recipient}")
                return True, "Message sent successfully"
            else:
                return False, f"Message rejected: {response}"

        except Exception as e:
            logger.error(f"Send mail error: {e}")
            return False, str(e)

    def quit(self):
        """Send QUIT and close the connection."""
        try:
            if self.socket and self.connected:
                self._send_command("QUIT")
        except Exception:
            pass
        finally:
            self._close()

    def _send_command(self, command):
        """Send a command and read the response."""
        try:
            cmd_bytes = (command + "\r\n").encode("utf-8")
            self.socket.sendall(cmd_bytes)
            return self._recv()
        except Exception as e:
            logger.error(f"Send command error: {e}")
            return None

    def _recv(self):
        """Read response from server."""
        try:
            data = self.socket.recv(4096)
            return data.decode("utf-8", errors="replace").strip()
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None

    def _close(self):
        """Close the socket."""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
