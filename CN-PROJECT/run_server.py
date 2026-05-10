import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.smtp_server import SmtpServer


def main():
    print("=" * 50)
    print("  SMTP Mail Server")
    print("  CS3001 - Computer Networks Project")
    print("  FAST-NUCES, Karachi (Spring 2026)")
    print("=" * 50)
    print()

    if not os.path.exists("data/smtp_server.db"):
        print("[WARNING] Database not found!")
        print("Run 'python setup_database.py' first to initialize the database.")
        print()
        response = input("Initialize database now? (y/n): ").strip().lower()
        if response == "y":
            from setup_database import main as setup_main
            setup_main()
            print()
        else:
            print("Exiting. Please run setup_database.py first.")
            return

    server = SmtpServer("config.json")

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()


if __name__ == "__main__":
    main()
