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
| huzaifa@nu.edu.pk | huzaifa123 |
| haris@nu.edu.pk | haris123 |
| ali.khan@gmail.com | ali123 |
| ahmed.raza@gmail.com | ahmed123 |
| fatima.zahra@yahoo.com | fatima123 |
| ayesha.sid@yahoo.com | ayesha123 |
| omar.farooq@hotmail.com | omar123 |
| zain.malik@hotmail.com | zain123 |
| sara.ahmed@outlook.com | sara123 |
| bilal.hassan@outlook.com | bilal123 |


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


## Demo

https://github.com/S-Huzaifa-Ali/Computer-Networks-Project/releases/download/v1.0/CN.Project.Demo.mp4


## References

- RFC 5321 – Simple Mail Transfer Protocol
- RFC 3207 – SMTP Service Extension for Secure SMTP over TLS
- Python smtplib Documentation
- Kurose, J. F., & Ross, K. W. (Computer Networking: A Top-Down Approach)
