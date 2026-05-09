import socket
import threading
from server.smtp_commands import SmtpCommandHandler
from utils.logger import server_logger as logger


class ClientHandler(threading.Thread):
    """Thread that handles a single SMTP client session."""
    def __init__(self, client_socket, client_address, auth_manager,
                 domain_manager, mail_queue, timeout=300):
        super().__init__(daemon=True)
        self.socket = client_socket
        self.address = client_address
        self.timeout = timeout

        self.handler = SmtpCommandHandler(auth_manager, domain_manager, mail_queue)
        self.name = f"Client-{client_address[0]}:{client_address[1]}"

    def run(self):
        """Main client loop - read commands, process, send responses."""
        logger.info(f"New connection from {self.address[0]}:{self.address[1]}")

        try:
            self.socket.settimeout(self.timeout)

            greeting = self.handler.get_greeting()
            self._send(greeting)

            buffer = ""
            while True:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        logger.info(f"Client disconnected: {self.address}")
                        break

                    buffer += data.decode("utf-8", errors="replace")

                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        response = self.handler.process_command(line)

                        if response:
                            self._send(response)

                        if line.strip().upper() == "QUIT":
                            return

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        response = self.handler.process_command(line)

                        if response:
                            self._send(response)

                        if line.strip().upper() == "QUIT":
                            return

                except socket.timeout:
                    logger.warning(f"Client timed out: {self.address}")
                    self._send("421 Connection timed out\r\n")
                    break
                except ConnectionResetError:
                    logger.info(f"Client connection reset: {self.address}")
                    break

        except Exception as e:
            logger.error(f"Error handling client {self.address}: {e}")
        finally:
            self._cleanup()

    def _send(self, data):
        """Send a response string to the client."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            self.socket.sendall(data)
        except (BrokenPipeError, ConnectionResetError):
            logger.warning(f"Failed to send to {self.address} - connection broken")

    def _cleanup(self):
        """Close the client socket."""
        try:
            self.socket.close()
        except Exception:
            pass
        logger.info(f"Connection closed: {self.address[0]}:{self.address[1]}")
