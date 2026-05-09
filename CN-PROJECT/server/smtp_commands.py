import base64
from server.response_codes import *
from server.response_codes import build_response, build_multiline_response
from utils.validators import validate_email, clean_address, extract_domain
from utils.logger import server_logger as logger


STATE_CONNECTED = "CONNECTED"
STATE_GREETED = "GREETED"
STATE_AUTH_USERNAME = "AUTH_USERNAME"  
STATE_AUTH_PASSWORD = "AUTH_PASSWORD"   
STATE_AUTHENTICATED = "AUTHENTICATED"
STATE_MAIL_FROM = "MAIL_FROM_SET"
STATE_RCPT_TO = "RCPT_TO_SET"
STATE_DATA = "DATA_MODE"


class SmtpCommandHandler:
    def __init__(self, auth_manager, domain_manager, mail_queue):
        self.auth_manager = auth_manager
        self.domain_manager = domain_manager
        self.mail_queue = mail_queue

        self.state = STATE_CONNECTED
        self.client_domain = None
        self.authenticated_user = None
        self.mail_from = None
        self.rcpt_to = []
        self.data_buffer = []

        self._auth_username = None

    def get_greeting(self, server_domain="smtp.local"):
        """Generate the initial 220 greeting banner."""
        return build_response(SERVICE_READY, f"{server_domain} SMTP Server Ready")

    def process_command(self, raw_line):
        """
        Parse and handle a single line of SMTP input.
        Returns the response string to send back to the client.
        """
        line = raw_line.strip()

        if not line:
            return None  

        if self.state == STATE_DATA:
            return self._handle_data_line(line)

        if self.state == STATE_AUTH_USERNAME:
            return self._handle_auth_username(line)
        if self.state == STATE_AUTH_PASSWORD:
            return self._handle_auth_password(line)

        parts = line.split(" ", 1)
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""

        handlers = {
            "HELO": self._handle_helo,
            "EHLO": self._handle_ehlo,
            "AUTH": self._handle_auth,
            "MAIL": self._handle_mail,
            "RCPT": self._handle_rcpt,
            "DATA": self._handle_data,
            "RSET": self._handle_rset,
            "NOOP": self._handle_noop,
            "QUIT": self._handle_quit,
        }

        handler = handlers.get(command)
        if handler:
            return handler(args)
        else:
            logger.warning(f"Unrecognized command: {command}")
            return build_response(SYNTAX_ERROR, f"Command not recognized: {command}")

    def _handle_helo(self, args):
        """HELO <client-domain> - basic SMTP greeting."""
        if not args.strip():
            return build_response(ARGUMENT_ERROR, "HELO requires a domain argument")

        self.client_domain = args.strip()
        self.state = STATE_GREETED
        logger.info(f"HELO from {self.client_domain}")
        return build_response(OK, f"Hello {self.client_domain}, pleased to meet you")

    def _handle_ehlo(self, args):
        """EHLO <client-domain> - extended SMTP greeting with capabilities."""
        if not args.strip():
            return build_response(ARGUMENT_ERROR, "EHLO requires a domain argument")

        self.client_domain = args.strip()
        self.state = STATE_GREETED

        capabilities = [
            f"Hello {self.client_domain}",
            "AUTH LOGIN PLAIN",
            "STARTTLS",
            "8BITMIME",
            "SIZE 10485760",
        ]

        logger.info(f"EHLO from {self.client_domain}")
        return build_multiline_response(OK, capabilities)

    def _handle_auth(self, args):
        """AUTH LOGIN/PLAIN - start authentication."""
        if self.state not in (STATE_GREETED, STATE_AUTHENTICATED):
            return build_response(BAD_SEQUENCE, "Send EHLO/HELO first")

        parts = args.strip().split(" ", 1)
        mechanism = parts[0].upper() if parts else ""

        if mechanism == "LOGIN":
            self.state = STATE_AUTH_USERNAME
            prompt = base64.b64encode(b"Username:").decode()
            return f"334 {prompt}\r\n"

        elif mechanism == "PLAIN":
            if len(parts) < 2:
                return build_response(ARGUMENT_ERROR, "AUTH PLAIN requires credentials")
            return self._handle_auth_plain(parts[1])

        else:
            return build_response(ARGUMENT_ERROR, "Unsupported auth mechanism. Use LOGIN or PLAIN")

    def _handle_auth_username(self, line):
        """Receive base64-encoded username during AUTH LOGIN."""
        try:
            self._auth_username = base64.b64decode(line.strip()).decode("utf-8")
            self.state = STATE_AUTH_PASSWORD
            prompt = base64.b64encode(b"Password:").decode()
            return f"334 {prompt}\r\n"
        except Exception:
            self.state = STATE_GREETED
            return build_response(AUTH_FAILED, "Invalid username encoding")

    def _handle_auth_password(self, line):
        """Receive base64-encoded password during AUTH LOGIN."""
        try:
            password = base64.b64decode(line.strip()).decode("utf-8")
        except Exception:
            self.state = STATE_GREETED
            return build_response(AUTH_FAILED, "Invalid password encoding")

        if self.auth_manager.authenticate(self._auth_username, password):
            self.authenticated_user = self._auth_username
            self.state = STATE_AUTHENTICATED
            logger.info(f"User authenticated: {self._auth_username}")
            return build_response(AUTH_SUCCESS, "Authentication successful")
        else:
            self.state = STATE_GREETED
            self._auth_username = None
            return build_response(AUTH_FAILED, "Authentication failed")

    def _handle_auth_plain(self, credentials_b64):
        """Handle AUTH PLAIN mechanism (credentials in single base64 string)."""
        try:
            decoded = base64.b64decode(credentials_b64.strip()).decode("utf-8")
            parts = decoded.split("\0")
            if len(parts) == 3:
                username = parts[1]
                password = parts[2]
            elif len(parts) == 2:
                username = parts[0]
                password = parts[1]
            else:
                return build_response(AUTH_FAILED, "Invalid PLAIN credentials format")

            if self.auth_manager.authenticate(username, password):
                self.authenticated_user = username
                self.state = STATE_AUTHENTICATED
                logger.info(f"User authenticated (PLAIN): {username}")
                return build_response(AUTH_SUCCESS, "Authentication successful")
            else:
                self.state = STATE_GREETED
                return build_response(AUTH_FAILED, "Authentication failed")

        except Exception as e:
            self.state = STATE_GREETED
            logger.error(f"AUTH PLAIN error: {e}")
            return build_response(AUTH_FAILED, "Authentication error")

    def _handle_mail(self, args):
        """MAIL FROM:<sender@domain.com>"""
        if self.state not in (STATE_AUTHENTICATED,):
            return build_response(BAD_SEQUENCE, "Authenticate first (AUTH LOGIN)")

        upper_args = args.upper()
        if not upper_args.startswith("FROM:"):
            return build_response(ARGUMENT_ERROR, "Syntax: MAIL FROM:<address>")

        address = args[5:].strip() 
        address = clean_address(address)

        if not validate_email(address):
            return build_response(ARGUMENT_ERROR, f"Invalid sender address: {address}")

        self.mail_from = address
        self.rcpt_to = []  
        self.state = STATE_MAIL_FROM
        logger.info(f"MAIL FROM: {address}")
        return build_response(OK, f"Sender <{address}> OK")

    def _handle_rcpt(self, args):
        """RCPT TO:<recipient@domain.com>"""
        if self.state not in (STATE_MAIL_FROM, STATE_RCPT_TO):
            return build_response(BAD_SEQUENCE, "Send MAIL FROM first")

        upper_args = args.upper()
        if not upper_args.startswith("TO:"):
            return build_response(ARGUMENT_ERROR, "Syntax: RCPT TO:<address>")

        address = args[3:].strip()
        address = clean_address(address)

        if not validate_email(address):
            return build_response(ARGUMENT_ERROR, f"Invalid recipient address: {address}")

        domain = extract_domain(address)
        if not self.domain_manager.is_local_domain(domain):
            return build_response(MAILBOX_NOT_FOUND,
                                  f"Domain {domain} not handled by this server")

        if not self.auth_manager.user_exists(address):
            return build_response(MAILBOX_NOT_FOUND,
                                  f"User <{address}> not found")

        self.rcpt_to.append(address)
        self.state = STATE_RCPT_TO
        logger.info(f"RCPT TO: {address}")
        return build_response(OK, f"Recipient <{address}> OK")

    def _handle_data(self, args):
        """DATA - switch to message body input mode."""
        if self.state != STATE_RCPT_TO:
            return build_response(BAD_SEQUENCE, "Send RCPT TO first")

        self.data_buffer = []
        self.state = STATE_DATA
        logger.info("Entering DATA mode")
        return build_response(START_MAIL_INPUT)

    def _handle_data_line(self, line):
        """
        Process a line of message body.
        A single dot on a line by itself signals end of message.
        """
        if line == ".":
            return self._finish_data()
        else:
            if line.startswith(".."):
                line = line[1:]
            self.data_buffer.append(line)
            return None 

    def _finish_data(self):
        """Process the complete message after DATA termination."""
        raw_message = "\n".join(self.data_buffer)

        subject = ""
        body_lines = []
        header_done = False
        for line in self.data_buffer:
            if not header_done:
                if line == "":
                    header_done = True
                elif line.upper().startswith("SUBJECT:"):
                    subject = line[8:].strip()
            else:
                body_lines.append(line)

        body = "\n".join(body_lines) if body_lines else raw_message

        for recipient in self.rcpt_to:
            self.mail_queue.enqueue(
                self.mail_from, recipient, subject, body
            )
            logger.info(f"Message queued: {self.mail_from} -> {recipient}")

        self.mail_from = None
        self.rcpt_to = []
        self.data_buffer = []
        self.state = STATE_AUTHENTICATED

        return build_response(OK, "Message accepted for delivery")

    def _handle_rset(self, args):
        """RSET - reset the session state (but keep auth)."""
        self.mail_from = None
        self.rcpt_to = []
        self.data_buffer = []
        if self.authenticated_user:
            self.state = STATE_AUTHENTICATED
        else:
            self.state = STATE_GREETED if self.client_domain else STATE_CONNECTED
        logger.info("Session reset (RSET)")
        return build_response(OK, "Reset OK")

    def _handle_noop(self, args):
        """NOOP - do nothing, just respond OK."""
        return build_response(OK, "OK")

    def _handle_quit(self, args):
        """QUIT - end the session."""
        self.state = STATE_CONNECTED
        logger.info(f"Client quit: {self.client_domain or 'unknown'}")
        return build_response(SERVICE_CLOSING, "Bye, closing connection")
