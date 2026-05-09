import re


EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


def validate_email(address):
    """Check if an email address has valid format."""
    if not address or not isinstance(address, str):
        return False
    return EMAIL_PATTERN.match(address.strip()) is not None


def extract_domain(email):
    """Pull out the domain part from an email address."""
    if "@" not in email:
        return None
    return email.strip().split("@")[1].lower()


def extract_username(email):
    """Pull out the local part (username) from an email address."""
    if "@" not in email:
        return None
    return email.strip().split("@")[0].lower()


def clean_address(address):
    """
    Strip angle brackets from SMTP addresses.
    MAIL FROM:<user@domain.com> -> user@domain.com
    """
    addr = address.strip()
    if addr.startswith("<") and addr.endswith(">"):
        addr = addr[1:-1]
    return addr.strip().lower()


def validate_domain(domain, registered_domains):
    """Check if a domain is in our list of registered domains."""
    return domain.lower() in [d.lower() for d in registered_domains]
