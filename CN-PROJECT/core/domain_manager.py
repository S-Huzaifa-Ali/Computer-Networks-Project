import json
import os
from utils.logger import server_logger as logger


class DomainManager:
    """Registry of local domains that this server handles."""

    def __init__(self, config_path="config.json"):
        self.domains = []
        self._load_domains(config_path)

    def _load_domains(self, config_path):
        """Load domain list from the config file."""
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            self.domains = [d.lower() for d in config.get("domains", [])]
            logger.info(f"Loaded {len(self.domains)} domains: {self.domains}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Could not load domains from config: {e}")
            self.domains = [
                "alpha.local", "beta.local", "gamma.local",
                "delta.local", "omega.local"
            ]
            logger.info("Using default domain list")

    def is_local_domain(self, domain):
        """Check if we handle mail for this domain."""
        return domain.lower() in self.domains

    def get_all_domains(self):
        """Return the list of all registered domains."""
        return self.domains.copy()

    def get_domain_for_email(self, email):
        """Extract and validate the domain part of an email address."""
        if "@" not in email:
            return None
        domain = email.split("@")[1].lower()
        if self.is_local_domain(domain):
            return domain
        return None

    def can_deliver(self, recipient_email):
        domain = self.get_domain_for_email(recipient_email)
        return domain is not None
