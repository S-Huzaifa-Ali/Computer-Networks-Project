import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db_manager import DatabaseManager
from core.auth_manager import AuthManager


def seed_users(auth_manager):
    """
    Register the 10 default users across all 5 domains.
    These are the accounts students will use during the demo.
    """
    users = [
        ("huzaifa@nu.edu.pk", "huzaifa123", "Huzaifa"),
        ("haris@nu.edu.pk", "haris123", "Haris"),

        ("ali.khan@gmail.com", "ali123", "Ali"),
        ("ahmed.raza@gmail.com", "ahmed123", "Ahmed"),

        ("fatima.zahra@yahoo.com", "fatima123", "Fatima"),
        ("ayesha.sid@yahoo.com", "ayesha123", "Ayesha"),

        ("omar.farooq@hotmail.com", "omar123", "Omar"),
        ("zain.malik@hotmail.com", "zain123", "Zain"),

        ("sara.ahmed@outlook.com", "sara123", "Sara"),
        ("bilal.hassan@outlook.com", "bilal123", "Bilal"),
    ]

    print("Registering users...")
    for email, password, username in users:
        domain = email.split("@")[1]
        success = auth_manager.register_user(email, password, username, domain)
        status = "OK" if success else "ALREADY EXISTS"
        print(f"  [{status}] {email}")

    print(f"\nTotal: {len(users)} users registered across 5 domains")


def main():
    print("=" * 50)
    print("SMTP Mail Server - Database Setup")
    print("=" * 50)
    print()

    db_path = "data/smtp_server.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Old database removed.")

    db = DatabaseManager(db_path)
    auth = AuthManager(db)

    seed_users(auth)

    print()
    print("Database setup complete!")
    print("You can now start the server with: python run_server.py")
    print("Then start the client with: python run_client.py")


if __name__ == "__main__":
    main()
