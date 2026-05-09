# Implementation of an SMTP Mail Server

*CS3001 - Computer Networks | Spring 2026*
*FAST School of Computing, NUCES Karachi*

*Group Members:*
- Syed Huzaifa Ali (23K0004)
- Haris Ahmed (23K6005)

---

## Project Overview

This project implements a multi-domain SMTP mail server with a GUI client, built using Python. It simulates real-world email communication within a controlled environment, supporting 5 local domains and 10 registered users with cross-domain email delivery.

The system follows the client-server architecture where email clients communicate with the SMTP server using standard SMTP protocol commands as defined in RFC 5321.

## Features

- *SMTP Command Processing* — HELO, EHLO, AUTH, MAIL FROM, RCPT TO, DATA, RSET, NOOP, QUIT
- *User Authentication* — SHA-256 password hashing with random salt
- *Mail Queue* — Asynchronous delivery with retry logic (3 attempts)
- *TLS/SSL Support* — Optional self-signed certificate encryption
- *Multi-client Support* — Thread-per-client architecture
- *Persistent Storage* — SQLite database for users and messages
- *Mail Retrieval* — Simplified protocol for inbox/sent items
- *GUI Client* — Dark-themed interface with CustomTkinter
- *Logging* — Rotating file logs with console output
- *5 Domains* — alpha.local, beta.local, gamma.local, delta.local, omega.local
- *10 Users* — 2 per domain with Pakistani names

## Quick Start

### 1. Install Dependencies
bash
pip install -r requirements.txt


### 2. Initialize Database
bash
python setup_database.py


### 3. Start the Server
bash
python run_server.py


### 4. Start the GUI Client (in a new terminal)
bash
python run_client.py


### 5. Login
Use any of the registered accounts:

| Email | Password |
|---|---|
| huzaifa@alpha.local | huzaifa123 |
| haris@alpha.local | haris123 |
| ali@beta.local | ali123 |
| ahmed@beta.local | ahmed123 |
| fatima@gamma.local | fatima123 |
| ayesha@gamma.local | ayesha123 |
| omar@delta.local | omar123 |
| zain@delta.local | zain123 |
| sara@omega.local | sara123 |
| bilal@omega.local | bilal123 |

## Project Structure


CN-PROJECT/
├── config.json              # Server configuration
├── requirements.txt         # Python dependencies
├── setup_database.py        # Database initialization + user seeding
├── run_server.py            # Server entry point
├── run_client.py            # GUI client entry point
│
├── server/                  # SMTP server implementation
│   ├── smtp_server.py       # Main server listener
│   ├── client_handler.py    # Per-client thread handler
│   ├── smtp_commands.py     # SMTP command processing + state machine
│   ├── response_codes.py    # RFC 5321 response codes
│   └── retrieval_server.py  # Mail retrieval protocol
│
├── core/                    # Core business logic
│   ├── auth_manager.py      # User authentication + hashing
│   ├── db_manager.py        # SQLite database manager
│   ├── mail_store.py        # Email storage (inbox/sent)
│   ├── domain_manager.py    # Domain registry + routing
│   └── mail_queue.py        # Outgoing queue + delivery worker
│
├── client/                  # Client-side protocol handlers
│   ├── smtp_client.py       # SMTP client for sending mail
│   └── retrieval_client.py  # Retrieval client for inbox/sent
│
├── gui/                     # GUI application (CustomTkinter)
│   ├── app.py               # Root application window
│   ├── theme.py             # Dark theme constants
│   ├── login_frame.py       # Login screen
│   ├── dashboard.py         # Main dashboard + navigation
│   ├── compose_frame.py     # Email composition
│   ├── inbox_frame.py       # Inbox view
│   └── sent_frame.py        # Sent items view
│
├── utils/                   # Shared utilities
│   ├── logger.py            # Logging configuration
│   └── validators.py        # Email/domain validation
│
├── tests/                   # Test suite
│   ├── test_smtp.py         # SMTP command unit tests
│   ├── test_auth.py         # Authentication unit tests
│   └── test_integration.py  # End-to-end integration tests
│
├── certs/                   # SSL certificates (optional)
│   └── generate_certs.py    # Self-signed cert generator
│
├── logs/                    # Runtime log files
└── docs/                    # Documentation
    ├── ARCHITECTURE.md      # System architecture
    └── SETUP.md             # Detailed setup guide


## Running Tests

bash
# Unit tests (no server needed)
python -m pytest tests/test_smtp.py tests/test_auth.py -v

# Integration tests (server must be running)
python -m pytest tests/test_integration.py -v


## SMTP Response Codes

| Code | Meaning |
|---|---|
| 220 | Service ready |
| 221 | Closing connection |
| 235 | Authentication successful |
| 250 | OK |
| 354 | Start mail input |
| 421 | Service unavailable |
| 450 | Mailbox temporarily unavailable |
| 500 | Syntax error |
| 501 | Argument syntax error |
| 503 | Bad sequence of commands |
| 535 | Authentication failed |
| 550 | Mailbox not found |

## References

- RFC 5321 – Simple Mail Transfer Protocol
- RFC 3207 – SMTP Service Extension for Secure SMTP over TLS
- Python smtplib Documentation
- Kurose, J. F., & Ross, K. W. (Computer Networking: A Top-Down Approach)
