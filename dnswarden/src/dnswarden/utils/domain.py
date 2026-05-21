"""Domain utilities."""

import re


def normalize_domain(domain):
    """Normalize domain to lowercase without trailing dot."""
    if not domain:
        return ""
    return domain.strip().lower().rstrip(".")


def is_valid_domain(domain):
    """Check if domain is valid."""
    if not domain or len(domain) > 253:
        return False
    pattern = r"^(?!-)[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.?$"
    return bool(re.match(pattern, domain))


def split_domain(domain):
    """Split domain into labels."""
    return normalize_domain(domain).split(".")


def parent_domain(domain):
    """Get parent domain."""
    labels = split_domain(domain)
    if len(labels) > 1:
        return ".".join(labels[1:])
    return None
