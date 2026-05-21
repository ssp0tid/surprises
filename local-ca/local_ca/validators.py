"""Input validation for local-ca."""
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pathlib import Path


def validate_ca_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate CA name.
    
    Args:
        name: CA name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "CA name cannot be empty"
    
    if len(name) > 64:
        return False, "CA name must be 64 characters or less"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "CA name can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_cert_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate certificate name.
    
    Args:
        name: Certificate name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Certificate name cannot be empty"
    
    if len(name) > 64:
        return False, "Certificate name must be 64 characters or less"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "Certificate name can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_common_name(common_name: str) -> Tuple[bool, Optional[str]]:
    """Validate common name.
    
    Args:
        common_name: Common name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not common_name:
        return False, "Common name cannot be empty"
    
    if len(common_name) > 64:
        return False, "Common name must be 64 characters or less"
    
    # Allow various characters but validate format
    if not re.match(r'^[a-zA-Z0-9*._\s-]+$', common_name):
        return False, "Common name contains invalid characters"
    
    return True, None


def validate_validity_years(years: int) -> Tuple[bool, Optional[str]]:
    """Validate certificate validity years.
    
    Args:
        years: Number of years for validity
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if years < 1:
        return False, "Validity must be at least 1 year"
    
    if years > 30:
        return False, "Validity cannot exceed 30 years"
    
    return True, None


def validate_key_size(size: int) -> Tuple[bool, Optional[str]]:
    """Validate key size.
    
    Args:
        size: Key size in bits
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_sizes = [1024, 2048, 4096]
    
    if size not in valid_sizes:
        return False, f"Key size must be one of: {', '.join(map(str, valid_sizes))}"
    
    return True, None


def validate_san(san_list: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate Subject Alternative Names.
    
    Args:
        san_list: List of SAN strings
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not san_list:
        return True, None
    
    for san in san_list:
        san = san.strip()
        if not san:
            continue
        
        # Check for valid DNS name or IP
        if san.replace('.', '').replace(':', '').isdigit():
            # Could be IP address
            continue
        
        if not re.match(r'^[a-zA-Z0-9*._-]+$', san):
            return False, f"Invalid SAN format: {san}"
        
        if len(san) > 253:
            return False, f"SAN too long (max 253 chars): {san}"
    
    return True, None


def validate_country_code(country: str) -> Tuple[bool, Optional[str]]:
    """Validate country code.
    
    Args:
        country: Two-letter country code
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not country:
        return True, None  # Optional field
    
    if len(country) != 2:
        return False, "Country code must be 2 letters"
    
    if not country.isalpha():
        return False, "Country code must only contain letters"
    
    if not country.isupper():
        return False, "Country code must be uppercase"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address.
    
    Args:
        email: Email address
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return True, None  # Optional field
    
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_path(path: str) -> Tuple[bool, Optional[str]]:
    """Validate file path.
    
    Args:
        path: File path
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    try:
        p = Path(path)
        if p.exists() and not p.is_file():
            return False, "Path exists but is not a file"
    except Exception as e:
        return False, f"Invalid path: {e}"
    
    return True, None


def validate_pem_data(data: str) -> Tuple[bool, Optional[str]]:
    """Validate PEM-encoded data.
    
    Args:
        data: PEM-encoded string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data:
        return False, "PEM data cannot be empty"
    
    if not data.startswith('-----BEGIN '):
        return False, "Invalid PEM format: missing header"
    
    if '-----END ' not in data:
        return False, "Invalid PEM format: missing footer"
    
    return True, None


def validate_passphrase(passphrase: str, confirm: str = None) -> Tuple[bool, Optional[str]]:
    """Validate passphrase.
    
    Args:
        passphrase: Passphrase to validate
        confirm: Optional confirmation passphrase
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not passphrase:
        return False, "Passphrase cannot be empty"
    
    if len(passphrase) < 4:
        return False, "Passphrase must be at least 4 characters"
    
    if confirm is not None and passphrase != confirm:
        return False, "Passphrases do not match"
    
    return True, None


def validate_positive_int(value: str, field_name: str = "value") -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate positive integer.
    
    Args:
        value: String to parse as integer
        field_name: Name of the field for error messages
        
    Returns:
        Tuple of (is_valid, error_message, parsed_int)
    """
    if not value:
        return False, f"{field_name} cannot be empty", None
    
    try:
        num = int(value)
        if num < 1:
            return False, f"{field_name} must be positive", None
        return True, None, num
    except ValueError:
        return False, f"{field_name} must be a valid integer", None


def calculate_expiry_date(years: int) -> datetime:
    """Calculate expiry date from now + years.
    
    Args:
        years: Number of years
        
    Returns:
        Expiry datetime
    """
    from dateutil.relativedelta import relativedelta
    return datetime.now() + relativedelta(years=years)


def validate_cert_not_after(not_after: datetime) -> Tuple[bool, Optional[str]]:
    """Validate certificate not_after date.
    
    Args:
        not_after: Expiry date
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not_after <= datetime.now():
        return False, "Certificate not_after date must be in the future"
    
    # Max 30 years for CA, 10 years for end-entity
    max_date = datetime.now() + timedelta(days=30*365)
    if not_after > max_date:
        return False, "Certificate validity cannot exceed 30 years"
    
    return True, None