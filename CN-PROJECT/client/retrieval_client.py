import socket
import json
from utils.logger import server_logger as logger


class RetrievalClient:
    """Client for fetching inbox/sent mail from the retrieval server."""

    def __init__(self, host="127.0.0.1", port=2526, timeout=15):
        self.host = host
        self.port = port
        self.timeout = timeout

    def _connect_and_auth(self, email, password):
        """Open a connection and authenticate. Returns socket or None."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))

            # read greeting
            greeting = sock.recv(4096).decode("utf-8").strip()
            if not greeting.startswith("+OK"):
                sock.close()
                return None

            # authenticate
            sock.sendall(f"AUTH {email} {password}\r\n".encode("utf-8"))
            response = sock.recv(4096).decode("utf-8").strip()
            if not response.startswith("+OK"):
                sock.close()
                return None

            return sock

        except Exception as e:
            logger.error(f"Retrieval connect error: {e}")
            return None

    def get_inbox(self, email, password):
        """Fetch inbox messages for the authenticated user."""
        sock = self._connect_and_auth(email, password)
        if not sock:
            return []

        try:
            sock.sendall(b"LIST INBOX\r\n")
            response = self._recv_full(sock)
            sock.sendall(b"QUIT\r\n")
            sock.close()

            if response and response.startswith("+OK "):
                json_data = response[4:]
                return json.loads(json_data)
            return []

        except Exception as e:
            logger.error(f"Get inbox error: {e}")
            return []
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def get_sent(self, email, password):
        """Fetch sent messages for the authenticated user."""
        sock = self._connect_and_auth(email, password)
        if not sock:
            return []

        try:
            sock.sendall(b"LIST SENT\r\n")
            response = self._recv_full(sock)
            sock.sendall(b"QUIT\r\n")
            sock.close()

            if response and response.startswith("+OK "):
                json_data = response[4:]
                return json.loads(json_data)
            return []

        except Exception as e:
            logger.error(f"Get sent error: {e}")
            return []
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def mark_read(self, email, password, message_id):
        """Mark a message as read on the server."""
        sock = self._connect_and_auth(email, password)
        if not sock:
            return False

        try:
            sock.sendall(f"READ {message_id}\r\n".encode("utf-8"))
            response = self._recv_full(sock)
            sock.sendall(b"QUIT\r\n")
            return response and response.startswith("+OK")
        except Exception:
            return False
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def get_unread_count(self, email, password):
        """Get the unread message count."""
        sock = self._connect_and_auth(email, password)
        if not sock:
            return 0

        try:
            sock.sendall(b"UNREAD\r\n")
            response = sock.recv(4096).decode("utf-8").strip()
            sock.sendall(b"QUIT\r\n")
            sock.close()

            if response and response.startswith("+OK "):
                return int(response[4:])
            return 0
        except Exception:
            return 0
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _recv_full(self, sock):
        data = b""
        while True:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
                # check if we got a complete response
                if b"\r\n" in data or b"\n" in data:
                    break
            except socket.timeout:
                break
        return data.decode("utf-8", errors="replace").strip()
