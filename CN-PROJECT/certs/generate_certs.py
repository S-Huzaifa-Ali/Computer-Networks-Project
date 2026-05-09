import subprocess
import os
import sys


def generate_self_signed_cert():
    """Generate self-signed SSL certificate using openssl."""
    cert_dir = os.path.dirname(os.path.abspath(__file__))
    cert_file = os.path.join(cert_dir, "server.crt")
    key_file = os.path.join(cert_dir, "server.key")

    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("Certificates already exist:")
        print(f"  Certificate: {cert_file}")
        print(f"  Private key: {key_file}")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            return

    print("Generating self-signed SSL certificate...")
    print("(Requires openssl to be installed)")
    print()

    try:
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", key_file,
            "-out", cert_file,
            "-days", "365",
            "-nodes", 
            "-subj", "/C=PK/ST=Sindh/L=Karachi/O=FAST-NUCES/CN=smtp.local"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Certificate generated successfully!")
            print(f"  Certificate: {cert_file}")
            print(f"  Private key: {key_file}")
            print(f"  Valid for: 365 days")
            print(f"  Subject: /C=PK/ST=Sindh/L=Karachi/O=FAST-NUCES/CN=smtp.local")
        else:
            print(f"Error: {result.stderr}")
            print()
            print("If openssl is not installed, you can skip TLS.")
            print("The server will run without TLS automatically.")

    except FileNotFoundError:
        print("openssl not found on PATH.")
        print("TLS is optional - the server works fine without it.")
        print()
        print("To install openssl on Windows:")
        print("  1. Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("  2. Or install via: choco install openssl")


if __name__ == "__main__":
    generate_self_signed_cert()
