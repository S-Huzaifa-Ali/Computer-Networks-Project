import socket
import threading
import json
from utils.logger import server_logger as logger


class RetrievalServer:
    """Simple mail retrieval server for the GUI client."""

    def __init__(self, host, port, auth_manager, mail_store):
        self.host = host
        self.port = port
        self.auth_manager = auth_manager
        self.mail_store = mail_store
        self._running = False
        self._socket = None

    def start(self):
        """Start listening for retrieval connections."""
        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.settimeout(1.0)

        try:
            self._socket.bind((self.host, self.port))
            self._socket.listen(5)
            logger.info(f"Retrieval server listening on {self.host}:{self.port}")

            while self._running:
                try:
                    client_sock, addr = self._socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_sock, addr),
                        daemon=True
                    )
                    thread.start()
                except socket.timeout:
                    continue
                except OSError:
                    break

        except OSError as e:
            logger.error(f"Retrieval server bind error: {e}")
        finally:
            if self._socket:
                self._socket.close()

    def stop(self):
        """Stop the retrieval server."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass

    def _handle_client(self, sock, addr):
        """Handle a single retrieval client connection."""
        logger.info(f"Retrieval connection from {addr}")
        authenticated_user = None

        try:
            sock.settimeout(120)
            sock.sendall(b"+OK Retrieval server ready\r\n")

            buffer = ""
            while True:
                data = sock.recv(4096)
                if not data:
                    break

                buffer += data.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    parts = line.split(" ", 2)
                    cmd = parts[0].upper()

                    if cmd == "AUTH" and len(parts) >= 3:
                        email = parts[1]
                        password = parts[2]
                        if self.auth_manager.authenticate(email, password):
                            authenticated_user = email
                            sock.sendall(b"+OK Authenticated\r\n")
                        else:
                            sock.sendall(b"-ERR Authentication failed\r\n")

                    elif cmd == "LIST" and len(parts) >= 2:
                        if not authenticated_user:
                            sock.sendall(b"-ERR Not authenticated\r\n")
                            continue

                        mailbox = parts[1].upper()
                        if mailbox == "INBOX":
                            messages = self.mail_store.get_inbox(authenticated_user)
                        elif mailbox == "SENT":
                            messages = self.mail_store.get_sent(authenticated_user)
                        else:
                            sock.sendall(b"-ERR Unknown mailbox\r\n")
                            continue

                        payload = json.dumps(messages)
                        response = f"+OK {payload}\r\n"
                        sock.sendall(response.encode("utf-8"))

                    elif cmd == "READ" and len(parts) >= 2:
                        if not authenticated_user:
                            sock.sendall(b"-ERR Not authenticated\r\n")
                            continue

                        try:
                            msg_id = int(parts[1])
                            message = self.mail_store.get_message(msg_id)
                            if message:
                                self.mail_store.mark_as_read(msg_id)
                                payload = json.dumps(message)
                                sock.sendall(f"+OK {payload}\r\n".encode("utf-8"))
                            else:
                                sock.sendall(b"-ERR Message not found\r\n")
                        except ValueError:
                            sock.sendall(b"-ERR Invalid message ID\r\n")

                    elif cmd == "UNREAD":
                        if not authenticated_user:
                            sock.sendall(b"-ERR Not authenticated\r\n")
                            continue
                        count = self.mail_store.get_unread_count(authenticated_user)
                        sock.sendall(f"+OK {count}\r\n".encode("utf-8"))

                    elif cmd == "QUIT":
                        sock.sendall(b"+OK Bye\r\n")
                        return

                    else:
                        sock.sendall(b"-ERR Unknown command\r\n")

        except socket.timeout:
            logger.info(f"Retrieval client timed out: {addr}")
        except Exception as e:
            logger.error(f"Retrieval handler error: {e}")
        finally:
            sock.close()
            logger.info(f"Retrieval connection closed: {addr}")
