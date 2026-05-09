import socket
import threading
import json
import ssl
import os
from server.client_handler import ClientHandler
from server.retrieval_server import RetrievalServer
from core.db_manager import DatabaseManager
from core.auth_manager import AuthManager
from core.domain_manager import DomainManager
from core.mail_store import MailStore
from core.mail_queue import MailQueue
from utils.logger import server_logger as logger


class SmtpServer:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)

        server_cfg = self.config["server"]
        self.host = server_cfg["host"]
        self.smtp_port = server_cfg["smtp_port"]
        self.retrieval_port = server_cfg["retrieval_port"]
        self.max_clients = server_cfg["max_clients"]
        self.timeout = server_cfg["timeout"]

        db_path = self.config["database"]["path"]
        self.db_manager = DatabaseManager(db_path)
        self.auth_manager = AuthManager(self.db_manager)
        self.domain_manager = DomainManager(config_path)
        self.mail_store = MailStore(self.db_manager)
        self.mail_queue = MailQueue(
            self.db_manager, self.mail_store, self.auth_manager, self.config
        )

        self.retrieval_server = RetrievalServer(
            self.host, self.retrieval_port,
            self.auth_manager, self.mail_store
        )

        self._running = False
        self._server_socket = None
        self._active_clients = []

        self.ssl_context = None
        if self.config.get("tls", {}).get("enabled", False):
            self._setup_tls()

    def _setup_tls(self):
        """Set up SSL context for secure connections."""
        tls_config = self.config.get("tls", {})
        cert_file = tls_config.get("cert_file", "certs/server.crt")
        key_file = tls_config.get("key_file", "certs/server.key")

        if os.path.exists(cert_file) and os.path.exists(key_file):
            try:
                self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                self.ssl_context.load_cert_chain(cert_file, key_file)
                logger.info("TLS configured successfully")
            except Exception as e:
                logger.warning(f"TLS setup failed, running without TLS: {e}")
                self.ssl_context = None
        else:
            logger.info("TLS cert/key not found - run generate_certs.py first. Continuing without TLS.")

    def start(self):
        """Start all server components."""
        logger.info("=" * 50)
        logger.info("SMTP Mail Server Starting Up")
        logger.info("=" * 50)

        self.mail_queue.start_worker()
        logger.info("Mail queue worker started")

        retrieval_thread = threading.Thread(
            target=self.retrieval_server.start, daemon=True
        )
        retrieval_thread.start()
        logger.info(f"Retrieval server started on port {self.retrieval_port}")

        domains = self.domain_manager.get_all_domains()
        logger.info(f"Serving domains: {', '.join(domains)}")

        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self._server_socket.bind((self.host, self.smtp_port))
            self._server_socket.listen(self.max_clients)
            self._server_socket.settimeout(1.0) 

            logger.info(f"SMTP server listening on {self.host}:{self.smtp_port}")
            logger.info("Press Ctrl+C to stop the server")
            print(f"\n[SERVER] SMTP server running on {self.host}:{self.smtp_port}")
            print(f"[SERVER] Retrieval server on {self.host}:{self.retrieval_port}")
            print(f"[SERVER] Domains: {', '.join(domains)}")
            print("[SERVER] Press Ctrl+C to stop\n")

            self._accept_loop()

        except OSError as e:
            logger.error(f"Could not bind to port {self.smtp_port}: {e}")
            print(f"[ERROR] Port {self.smtp_port} already in use. Stop any running servers first.")
        except KeyboardInterrupt:
            logger.info("Server shutdown requested (Ctrl+C)")
        finally:
            self.stop()

    def _accept_loop(self):
        """Accept incoming connections in a loop."""
        while self._running:
            try:
                client_socket, client_address = self._server_socket.accept()

                if self.ssl_context:
                    try:
                        client_socket = self.ssl_context.wrap_socket(
                            client_socket, server_side=True
                        )
                    except ssl.SSLError as e:
                        logger.warning(f"TLS handshake failed from {client_address}: {e}")
                        client_socket.close()
                        continue

                handler = ClientHandler(
                    client_socket, client_address,
                    self.auth_manager, self.domain_manager,
                    self.mail_queue, self.timeout
                )
                handler.start()
                self._active_clients.append(handler)

                self._active_clients = [t for t in self._active_clients if t.is_alive()]

            except socket.timeout:
                continue  
            except OSError:
                if self._running:
                    logger.error("Socket accept error")
                break

    def stop(self):
        """Gracefully shut down all server components."""
        logger.info("Shutting down server...")
        self._running = False

        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass

        self.mail_queue.stop_worker()
        self.retrieval_server.stop()

        logger.info("Server stopped")
        print("[SERVER] Server stopped.")

    def get_status(self):
        """Return current server status info for the GUI."""
        active = len([t for t in self._active_clients if t.is_alive()])
        queue_status = self.mail_queue.get_queue_status()
        return {
            "running": self._running,
            "host": self.host,
            "smtp_port": self.smtp_port,
            "retrieval_port": self.retrieval_port,
            "active_connections": active,
            "domains": self.domain_manager.get_all_domains(),
            "queue": queue_status,
        }
