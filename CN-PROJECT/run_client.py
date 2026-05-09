"""
SMTP Mail Client (GUI) entry point.
Launches the CustomTkinter GUI application.

Usage: python run_client.py
"""

import sys
import os

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import MailClientApp


def main():
    print("Starting SMTP Mail Client...")
    print("Make sure the server is running (python run_server.py)")
    print()

    app = MailClientApp()
    app.mainloop()


if __name__ == "__main__":
    main()
