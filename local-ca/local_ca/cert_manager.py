"""Certificate management logic for local-ca."""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from . import crypto_utils, database, validators


def create_root_ca(
    name: str,
    common_name: str,
    country: Optional[str] = None,
    state: Optional[str] = None,
    locality: Optional[str] = None,
    organization: Optional[str] = None,
    validity_years: int = 10,
    key_size: int = 4096
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Create a new root CA.
    
    Args:
        name: CA name (unique identifier)
        common_name: Common name for the CA
        country: Country code
        state: State or province
        locality: Locality
        organization: Organization name
        validity_years: Validity in years
        key_size: Key size in bits
        
    Returns:
        Tuple of (success, error_message, ca_info)
    """
    # Validate inputs
    is_valid, error = validators.validate_ca_name(name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_common_name(common_name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_validity_years(validity_years)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_key_size(key_size)
    if not is_valid:
        return False, error, None
    
    if country:
        is_valid, error = validators.validate_country_code(country)
        if not is_valid:
            return False, error, None
    
    # Create subject
    subject = crypto_utils.create_subject(
        common_name=common_name,
        country=country,
        state=state,
        locality=locality,
        organization=organization
    )
    
    # Generate key
    key = crypto_utils.generate_key(key_size=key_size)
    
    # Generate serial number
    serial_number = crypto_utils.generate_serial_number()
    
    # Calculate validity dates
    not_before = datetime.now()
    from dateutil.relativedelta import relativedelta
    not_after = not_before + relativedelta(years=validity_years)
    
    # Create self-signed certificate
    cert = crypto_utils.create_ca_certificate(
        key=key,
        subject=subject,
        issuer=subject,
        serial_number=serial_number,
        not_before=not_before,
        not_after=not_after,
        is_ca=True,
        path_length=None  # Unlimited path length for root CA
    )
    
    # Save files
    cert_dir = database.get_cert_dir()
    
    # Save private key
    key_path = cert_dir / f"{name}-key.pem"
    crypto_utils.save_private_key(key, key_path)
    
    # Save certificate
    cert_path = cert_dir / f"{name}.pem"
    crypto_utils.save_certificate(cert, cert_path)
    
    # Save to database
    ca_id = database.create_ca(
        name=name,
        ca_type='root',
        subject=crypto_utils.get_name_string(subject),
        issuer=crypto_utils.get_name_string(subject),  # Self-signed
        not_before=not_before,
        not_after=not_after,
        serial_number=str(serial_number),
        parent_id=None,
        is_ca=True,
        cert_path=str(cert_path),
        key_path=str(key_path)
    )
    
    return True, None, {
        'id': ca_id,
        'name': name,
        'common_name': common_name,
        'type': 'root',
        'cert_path': str(cert_path),
        'key_path': str(key_path),
    }


def create_intermediate_ca(
    name: str,
    common_name: str,
    parent_ca_id: int,
    country: Optional[str] = None,
    state: Optional[str] = None,
    locality: Optional[str] = None,
    organization: Optional[str] = None,
    validity_years: int = 5,
    key_size: int = 4096
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Create an intermediate CA signed by a parent CA.
    
    Args:
        name: CA name (unique identifier)
        common_name: Common name for the CA
        parent_ca_id: ID of the parent CA
        country: Country code
        state: State or province
        locality: Locality
        organization: Organization name
        validity_years: Validity in years
        key_size: Key size in bits
        
    Returns:
        Tuple of (success, error_message, ca_info)
    """
    # Validate inputs
    is_valid, error = validators.validate_ca_name(name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_common_name(common_name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_validity_years(validity_years)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_key_size(key_size)
    if not is_valid:
        return False, error, None
    
    # Get parent CA
    parent_ca = database.get_ca(parent_ca_id)
    if not parent_ca:
        return False, f"Parent CA with ID {parent_ca_id} not found", None
    
    # Load parent key
    parent_key = crypto_utils.load_private_key(Path(parent_ca['key_path']))
    parent_cert = crypto_utils.load_certificate(Path(parent_ca['cert_path']))
    
    # Create subject
    subject = crypto_utils.create_subject(
        common_name=common_name,
        country=country,
        state=state,
        locality=locality,
        organization=organization
    )
    
    # Generate key
    key = crypto_utils.generate_key(key_size=key_size)
    
    # Generate serial number
    serial_number = crypto_utils.generate_serial_number()
    
    # Calculate validity dates
    not_before = datetime.now()
    from dateutil.relativedelta import relativedelta
    not_after = not_before + relativedelta(years=validity_years)
    
    # Create CA certificate signed by parent
    cert = crypto_utils.create_ca_certificate(
        key=key,
        subject=subject,
        issuer=parent_cert.subject,
        serial_number=serial_number,
        not_before=not_before,
        not_after=not_after,
        is_ca=True,
        path_length=0  # Can't sign other CAs
    )
    
    # Save files
    cert_dir = database.get_cert_dir()
    
    # Save private key
    key_path = cert_dir / f"{name}-key.pem"
    crypto_utils.save_private_key(key, key_path)
    
    # Save certificate
    cert_path = cert_dir / f"{name}.pem"
    crypto_utils.save_certificate(cert, cert_path)
    
    # Save to database
    ca_id = database.create_ca(
        name=name,
        ca_type='intermediate',
        subject=crypto_utils.get_name_string(subject),
        issuer=crypto_utils.get_name_string(parent_cert.subject),
        not_before=not_before,
        not_after=not_after,
        serial_number=str(serial_number),
        parent_id=parent_ca_id,
        is_ca=True,
        cert_path=str(cert_path),
        key_path=str(key_path)
    )
    
    return True, None, {
        'id': ca_id,
        'name': name,
        'common_name': common_name,
        'type': 'intermediate',
        'parent_id': parent_ca_id,
        'cert_path': str(cert_path),
        'key_path': str(key_path),
    }


def create_tls_certificate(
    name: str,
    common_name: str,
    ca_id: int,
    country: Optional[str] = None,
    state: Optional[str] = None,
    locality: Optional[str] = None,
    organization: Optional[str] = None,
    email: Optional[str] = None,
    san: Optional[List[str]] = None,
    validity_years: int = 1,
    key_size: int = 2048
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Create a TLS certificate.
    
    Args:
        name: Certificate name (unique identifier)
        common_name: Common name (typically hostname)
        ca_id: ID of the signing CA
        country: Country code
        state: State or province
        locality: Locality
        organization: Organization name
        email: Email address
        san: List of Subject Alternative Names
        validity_years: Validity in years
        key_size: Key size in bits
        
    Returns:
        Tuple of (success, error_message, cert_info)
    """
    # Validate inputs
    is_valid, error = validators.validate_cert_name(name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_common_name(common_name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_validity_years(validity_years)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_key_size(key_size)
    if not is_valid:
        return False, error, None
    
    if san:
        is_valid, error = validators.validate_san(san)
        if not is_valid:
            return False, error, None
    
    # Get CA
    ca = database.get_ca(ca_id)
    if not ca:
        return False, f"CA with ID {ca_id} not found", None
    
    # Load CA key
    ca_key = crypto_utils.load_private_key(Path(ca['key_path']))
    ca_cert = crypto_utils.load_certificate(Path(ca['cert_path']))
    
    # Create subject
    subject = crypto_utils.create_subject(
        common_name=common_name,
        country=country,
        state=state,
        locality=locality,
        organization=organization,
        email_address=email
    )
    
    # Generate key
    key = crypto_utils.generate_key(key_size=key_size)
    
    # Generate serial number
    serial_number = crypto_utils.generate_serial_number()
    
    # Calculate validity dates
    not_before = datetime.now()
    from dateutil.relativedelta import relativedelta
    not_after = not_before + relativedelta(years=validity_years)
    
    # Create TLS certificate
    cert = crypto_utils.create_tls_certificate(
        key=key,
        ca_key=ca_key,
        ca_cert=ca_cert,
        subject=subject,
        serial_number=serial_number,
        not_before=not_before,
        not_after=not_after,
        san=san
    )
    
    # Save files
    cert_dir = database.get_cert_dir()
    
    # Save private key
    key_path = cert_dir / f"{name}-key.pem"
    crypto_utils.save_private_key(key, key_path)
    
    # Save certificate
    cert_path = cert_dir / f"{name}.pem"
    crypto_utils.save_certificate(cert, cert_path)
    
    # Save to database
    cert_id = database.create_certificate(
        ca_id=ca_id,
        name=name,
        common_name=common_name,
        subject=crypto_utils.get_name_string(subject),
        serial_number=str(serial_number),
        not_before=not_before,
        not_after=not_after,
        san=san,
        cert_path=str(cert_path),
        key_path=str(key_path)
    )
    
    return True, None, {
        'id': cert_id,
        'name': name,
        'common_name': common_name,
        'cert_path': str(cert_path),
        'key_path': str(key_path),
    }


def sign_csr_request(
    csr_data: str,
    ca_id: int,
    name: str,
    validity_years: int = 1
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Sign a CSR.
    
    Args:
        csr_data: PEM-encoded CSR data
        ca_id: ID of the signing CA
        name: Certificate name for the signed certificate
        validity_years: Validity in years
        
    Returns:
        Tuple of (success, error_message, cert_info)
    """
    # Validate inputs
    is_valid, error = validators.validate_cert_name(name)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_pem_data(csr_data)
    if not is_valid:
        return False, error, None
    
    is_valid, error = validators.validate_validity_years(validity_years)
    if not is_valid:
        return False, error, None
    
    # Get CA
    ca = database.get_ca(ca_id)
    if not ca:
        return False, f"CA with ID {ca_id} not found", None
    
    # Load CA key
    ca_key = crypto_utils.load_private_key(Path(ca['key_path']))
    ca_cert = crypto_utils.load_certificate(Path(ca['cert_path']))
    
    # Parse CSR
    from io import StringIO
    from cryptography.x509 import load_pem_x509_csr
    
    try:
        csr = load_pem_x509_csr(csr_data.encode())
    except Exception as e:
        return False, f"Invalid CSR: {e}", None
    
    # Get subject from CSR
    subject = csr.subject
    
    # Generate serial number
    serial_number = crypto_utils.generate_serial_number()
    
    # Calculate validity dates
    not_before = datetime.now()
    from dateutil.relativedelta import relativedelta
    not_after = not_before + relativedelta(years=validity_years)
    
    # Sign the CSR
    cert = crypto_utils.sign_csr(
        csr=csr,
        ca_key=ca_key,
        ca_cert=ca_cert,
        serial_number=serial_number,
        not_before=not_before,
        not_after=not_after
    )
    
    # Save files
    cert_dir = database.get_cert_dir()
    
    # Save certificate
    cert_path = cert_dir / f"{name}.pem"
    crypto_utils.save_certificate(cert, cert_path)
    
    # Save to database (note: no private key for CSR-signed certs)
    cert_id = database.create_certificate(
        ca_id=ca_id,
        name=name,
        common_name=str(subject.get_attributes_for_oid(1)[0].value) if subject.get_attributes_for_oid(1) else 'Unknown',
        subject=crypto_utils.get_name_string(subject),
        serial_number=str(serial_number),
        not_before=not_before,
        not_after=not_after,
        cert_path=str(cert_path),
        key_path=None  # Private key not provided
    )
    
    return True, None, {
        'id': cert_id,
        'name': name,
        'common_name': str(subject.get_attributes_for_oid(1)[0].value) if subject.get_attributes_for_oid(1) else 'Unknown',
        'cert_path': str(cert_path),
    }


def export_certificate(
    cert_id: int,
    output_path: str,
    format: str = 'pem',
    passphrase: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Export a certificate in various formats.
    
    Args:
        cert_id: Certificate ID
        output_path: Output file path
        format: Export format (pem, p12)
        passphrase: Optional passphrase for P12
        
    Returns:
        Tuple of (success, error_message)
    """
    # Get certificate from database
    cert = database.get_certificate(cert_id)
    if not cert:
        return False, f"Certificate with ID {cert_id} not found"
    
    # Load certificate and key
    cert_obj = crypto_utils.load_certificate(Path(cert['cert_path']))
    
    # For CSR-signed certificates, we may not have the private key
    key = None
    if cert['key_path']:
        key = crypto_utils.load_private_key(Path(cert['key_path']))
    
    # Handle export based on format
    if format == 'pem':
        # Export as PEM bundle
        output = cert_obj.public_bytes(crypto_utils.serialization.Encoding.PEM)
        if key:
            output += key.private_bytes(
                encoding=crypto_utils.serialization.Encoding.PEM,
                format=crypto_utils.serialization.PrivateFormat.PKCS8,
                encryption_algorithm=crypto_utils.serialization.NoEncryption()
            )
        
        Path(output_path).write_bytes(output)
        
    elif format == 'p12':
        if not key:
            return False, "P12 export requires private key (not available for CSR-signed certificates)"
        
        p12_data = crypto_utils.create_p12(
            key=key,
            cert=cert_obj,
            name=cert['name'],
            passphrase=passphrase.encode() if passphrase else None
        )
        
        Path(output_path).write_bytes(p12_data)
        
    else:
        return False, f"Unsupported format: {format}"
    
    return True, None


def get_ca_chain(ca_id: int) -> List[Dict[str, Any]]:
    """Get the certificate chain for a CA.
    
    Args:
        ca_id: CA ID
        
    Returns:
        List of CA certificates in the chain
    """
    chain = []
    current_id = ca_id
    
    while current_id:
        ca = database.get_ca(current_id)
        if not ca:
            break
        
        chain.append(ca)
        
        if ca['type'] == 'root':
            break
        
        current_id = ca.get('parent_id')
    
    return chain


def get_cert_chain(cert_id: int) -> List[Dict[str, Any]]:
    """Get the certificate chain for a certificate.
    
    Args:
        cert_id: Certificate ID
        
    Returns:
        List of certificates in the chain (leaf to root)
    """
    cert = database.get_certificate(cert_id)
    if not cert:
        return []
    
    chain = [cert]
    
    # Get CA chain
    ca_chain = get_ca_chain(cert['ca_id'])
    chain.extend(ca_chain)
    
    return chain