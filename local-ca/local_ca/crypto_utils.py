"""Cryptographic utilities for certificate operations."""
import os
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_key(key_size: int = 2048, private_key_path: Optional[Path] = None) -> rsa.RSAPrivateKey:
    """Generate an RSA private key.
    
    Args:
        key_size: Key size in bits (2048 for certificates, 4096 for CAs)
        private_key_path: Optional path to save the key
        
    Returns:
        RSA private key object
    """
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    if private_key_path:
        save_private_key(key, private_key_path)
    
    return key


def save_private_key(key: rsa.RSAPrivateKey, path: Path, passphrase: Optional[bytes] = None) -> None:
    """Save a private key to a file.
    
    Args:
        key: RSA private key
        path: Path to save the key
        passphrase: Optional passphrase to encrypt the key
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    encryption = serialization.BestAvailableEncryption(passphrase) if passphrase else serialization.NoEncryption()
    
    with open(path, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        ))


def load_private_key(path: Path, passphrase: Optional[bytes] = None) -> rsa.RSAPrivateKey:
    """Load a private key from a file.
    
    Args:
        path: Path to the private key file
        passphrase: Optional passphrase to decrypt the key
        
    Returns:
        RSA private key object
    """
    with open(path, 'rb') as f:
        key_data = f.read()
    
    return serialization.load_pem_private_key(
        key_data,
        password=passphrase,
        backend=default_backend()
    )


def load_certificate(path: Path) -> x509.Certificate:
    """Load a certificate from a file.
    
    Args:
        path: Path to the certificate file
        
    Returns:
        Certificate object
    """
    with open(path, 'rb') as f:
        cert_data = f.read()
    
    return x509.load_pem_x509_certificate(cert_data, default_backend())


def save_certificate(cert: x509.Certificate, path: Path) -> None:
    """Save a certificate to a file.
    
    Args:
        cert: Certificate object
        path: Path to save the certificate
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def create_subject(
    common_name: str,
    organization: Optional[str] = None,
    organizational_unit: Optional[str] = None,
    locality: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    email_address: Optional[str] = None
) -> x509.Name:
    """Create an X.509 subject name.
    
    Args:
        common_name: Common name (CN)
        organization: Organization (O)
        organizational_unit: Organizational unit (OU)
        locality: Locality (L)
        state: State or province (ST)
        country: Country (C)
        email_address: Email address
        
    Returns:
        X.509 Name object
    """
    attributes = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    
    if organization:
        attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
    if organizational_unit:
        attributes.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit))
    if locality:
        attributes.append(x509.NameAttribute(NameOID.LOCALITY_NAME, locality))
    if state:
        attributes.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state))
    if country:
        attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
    if email_address:
        attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email_address))
    
    return x509.Name(attributes)


def create_ca_certificate(
    key: rsa.RSAPrivateKey,
    subject: x509.Name,
    issuer: x509.Name,
    serial_number: int,
    not_before: datetime,
    not_after: datetime,
    is_ca: bool = True,
    key_usage: Optional[tuple] = None,
    path_length: Optional[int] = None
) -> x509.Certificate:
    """Create a CA certificate.
    
    Args:
        key: Private key for signing
        subject: Subject name
        issuer: Issuer name (same as subject for self-signed)
        serial_number: Certificate serial number
        not_before: Valid from date
        not_after: Valid until date
        is_ca: Whether this is a CA certificate
        key_usage: Tuple of key usage OIDs
        path_length: Maximum path length for CA certificates
        
    Returns:
        Certificate object
    """
    if key_usage is None:
        key_usage = (
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            )
        )
    
    # Build extensions
    extensions = [
        x509.BasicConstraints(ca=is_ca, path_length=path_length),
        key_usage,
    ]
    
    if is_ca:
        extensions.append(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key())
        )
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(key.public_key())
    builder = builder.serial_number(serial_number)
    builder = builder.not_valid_before(not_before)
    builder = builder.not_valid_after(not_after)
    
    # Add each extension individually
    for ext in extensions:
        if isinstance(ext, x509.BasicConstraints):
            builder = builder.add_extension(ext, ExtensionOID.BASIC_CONSTRAINTS)
        elif isinstance(ext, x509.KeyUsage):
            builder = builder.add_extension(ext, ExtensionOID.KEY_USAGE)
        elif isinstance(ext, x509.SubjectKeyIdentifier):
            builder = builder.add_extension(ext, ExtensionOID.SUBJECT_KEY_IDENTIFIER)
    
    return builder.sign(key, hashes.SHA256(), default_backend())


def create_tls_certificate(
    key: rsa.RSAPrivateKey,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    subject: x509.Name,
    serial_number: int,
    not_before: datetime,
    not_after: datetime,
    san: Optional[List[str]] = None,
    key_usage: Optional[x509.KeyUsage] = None,
    ext_key_usage: Optional[x509.ExtendedKeyUsage] = None
) -> x509.Certificate:
    """Create a TLS/SSL certificate.
    
    Args:
        key: Private key for the certificate
        ca_key: CA private key for signing
        ca_cert: CA certificate
        subject: Subject name
        serial_number: Certificate serial number
        not_before: Valid from date
        not_after: Valid until date
        san: List of Subject Alternative Names
        key_usage: Key usage extension
        ext_key_usage: Extended key usage extension
        
    Returns:
        Certificate object
    """
    if key_usage is None:
        key_usage = x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            key_cert_sign=False,
            crl_sign=False,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
        )
    
    if ext_key_usage is None:
        ext_key_usage = x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH,
            ExtendedKeyUsageOID.CLIENT_AUTH,
        ])
    
    # Build extensions
    extensions = [
        key_usage,
        ext_key_usage,
    ]
    
    # Add SAN if provided
    if san:
        san_extensions = []
        for name in san:
            if name.replace('.', '').isdigit():
                # Could be IP address
                try:
                    import ipaddress
                    ip = ipaddress.ip_address(name)
                    san_extensions.append(x509.DNSName(name))
                except ValueError:
                    san_extensions.append(x509.DNSName(name))
            else:
                san_extensions.append(x509.DNSName(name))
        
        extensions.append(x509.SubjectAlternativeName(san_extensions))
    
    # Add Authority Key Identifier
    try:
        ski = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
        extensions.append(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski.value)
        )
    except x509.ExtensionNotFound:
        pass
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(ca_cert.subject)
    builder = builder.public_key(key.public_key())
    builder = builder.serial_number(serial_number)
    builder = builder.not_valid_before(not_before)
    builder = builder.not_valid_after(not_after)
    
    # Add each extension individually
    for ext in extensions:
        if isinstance(ext, x509.KeyUsage):
            builder = builder.add_extension(ext, ExtensionOID.KEY_USAGE)
        elif isinstance(ext, x509.ExtendedKeyUsage):
            builder = builder.add_extension(ext, ExtensionOID.EXTENDED_KEY_USAGE)
        elif isinstance(ext, x509.SubjectAlternativeName):
            builder = builder.add_extension(ext, ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        elif isinstance(ext, x509.AuthorityKeyIdentifier):
            builder = builder.add_extension(ext, ExtensionOID.AUTHORITY_KEY_IDENTIFIER)
    
    return builder.sign(ca_key, hashes.SHA256(), default_backend())


def sign_csr(
    csr: x509.CertificateSigningRequest,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    serial_number: int,
    not_before: datetime,
    not_after: datetime,
    san: Optional[List[str]] = None
) -> x509.Certificate:
    """Sign a Certificate Signing Request.
    
    Args:
        csr: CSR to sign
        ca_key: CA private key
        ca_cert: CA certificate
        serial_number: Certificate serial number
        not_before: Valid from date
        not_after: Valid until date
        san: Optional SAN overrides
        
    Returns:
        Signed certificate
    """
    # Get subject from CSR
    subject = csr.public_key()
    
    # Use SAN from CSR if not provided
    if san is None:
        try:
            san_ext = csr.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            san = [name.value for name in san_ext.value]
        except x509.ExtensionNotFound:
            san = []
    
    # Build extensions
    extensions = [
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            key_cert_sign=False,
            crl_sign=False,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
        ),
        x509.ExtendedKeyUsage([
            ExtendedKeyUsageOID.SERVER_AUTH,
            ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
    ]
    
    if san:
        san_list = []
        for name in san:
            try:
                import ipaddress
                ip = ipaddress.ip_address(name)
                san_list.append(x509.DNSName(name))
            except ValueError:
                san_list.append(x509.DNSName(name))
        
        extensions.append(x509.SubjectAlternativeName(san_list))
    
    # Add Authority Key Identifier
    try:
        ski = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
        extensions.append(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski.value)
        )
    except x509.ExtensionNotFound:
        pass
    
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(csr.subject)
    builder = builder.issuer_name(ca_cert.subject)
    builder = builder.public_key(csr.public_key())
    builder = builder.serial_number(serial_number)
    builder = builder.not_valid_before(not_before)
    builder = builder.not_valid_after(not_after)
    
    # Add each extension individually
    for ext in extensions:
        if isinstance(ext, x509.KeyUsage):
            builder = builder.add_extension(ext, ExtensionOID.KEY_USAGE)
        elif isinstance(ext, x509.ExtendedKeyUsage):
            builder = builder.add_extension(ext, ExtensionOID.EXTENDED_KEY_USAGE)
        elif isinstance(ext, x509.SubjectAlternativeName):
            builder = builder.add_extension(ext, ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        elif isinstance(ext, x509.AuthorityKeyIdentifier):
            builder = builder.add_extension(ext, ExtensionOID.AUTHORITY_KEY_IDENTIFIER)
    
    return builder.sign(ca_key, hashes.SHA256(), default_backend())


def load_csr(path: Path) -> x509.CertificateSigningRequest:
    """Load a CSR from a file.
    
    Args:
        path: Path to the CSR file
        
    Returns:
        CSR object
    """
    with open(path, 'rb') as f:
        csr_data = f.read()
    
    return x509.load_pem_x509_csr(csr_data, default_backend())


def generate_serial_number() -> int:
    """Generate a random serial number for certificates.
    
    Returns:
        Random serial number
    """
    return int.from_bytes(os.urandom(16), 'big') >> 1


def certificate_to_pem(cert: x509.Certificate) -> bytes:
    """Convert certificate to PEM format.
    
    Args:
        cert: Certificate object
        
    Returns:
        PEM-encoded certificate bytes
    """
    return cert.public_bytes(serialization.Encoding.PEM)


def key_to_pem(key: rsa.RSAPrivateKey, passphrase: Optional[bytes] = None) -> bytes:
    """Convert private key to PEM format.
    
    Args:
        key: Private key object
        passphrase: Optional passphrase to encrypt the key
        
    Returns:
        PEM-encoded key bytes
    """
    encryption = serialization.BestAvailableEncryption(passphrase) if passphrase else serialization.NoEncryption()
    
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption
    )


def create_p12(
    key: rsa.RSAPrivateKey,
    cert: x509.Certificate,
    ca_certs: Optional[List[x509.Certificate]] = None,
    name: str = "certificate",
    passphrase: Optional[bytes] = None
) -> bytes:
    """Create a PKCS#12 bundle.
    
    Args:
        key: Private key
        cert: Certificate
        ca_certs: Optional chain of CA certificates
        name: Friendly name for the certificate
        passphrase: Passphrase to encrypt the bundle
        
    Returns:
        PKCS#12 bytes
    """
    from cryptography.hazmat.primitives.serialization import pkcs12
    
    passphrase = passphrase or b""
    
    return pkcs12.serialize_key_and_certificates(
        name=name.encode() if isinstance(name, str) else name,
        key=key,
        cert=cert,
        cas=ca_certs,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase)
    )


def create_jks(
    key: rsa.RSAPrivateKey,
    cert: x509.Certificate,
    alias: str = "certificate",
    keystore_pass: str = "changeit",
    key_pass: Optional[str] = None
) -> bytes:
    """Create a JKS (Java KeyStore) file.
    
    Note: This is a simplified implementation. For production use,
    consider using keytool or the python-jks library.
    
    Args:
        key: Private key
        cert: Certificate
        alias: Alias for the entry
        keystore_pass: Keystore password
        key_pass: Key password (defaults to keystore_pass)
        
    Returns:
        JKS bytes
    """
    # For now, we'll export as PKCS#12 and indicate in README
    # Full JKS implementation would require additional dependencies
    raise NotImplementedError(
        "JKS export requires keytool or python-jks. "
        "Please use P12 format or run: keytool -importkeystore -srckeystore cert.p12 -srcstoretype PKCS12 -destkeystore cert.jks"
    )


def get_cert_info(cert: x509.Certificate) -> Dict[str, Any]:
    """Extract certificate information.
    
    Args:
        cert: Certificate object
        
    Returns:
        Dictionary with certificate details
    """
    info = {
        'subject': dict(cert.subject),
        'issuer': dict(cert.issuer),
        'serial_number': cert.serial_number,
        'not_before': cert.not_valid_before_utc,
        'not_after': cert.not_valid_after_utc,
        'is_ca': False,
        'san': [],
        'key_usage': [],
        'ext_key_usage': [],
    }
    
    # Get extensions
    for ext in cert.extensions:
        if isinstance(ext, x509.BasicConstraints):
            info['is_ca'] = ext.ca
        elif isinstance(ext, x509.SubjectAlternativeName):
            info['san'] = [str(name) for name in ext.value]
        elif isinstance(ext, x509.KeyUsage):
            info['key_usage'] = ext
        elif isinstance(ext, x509.ExtendedKeyUsage):
            info['ext_key_usage'] = [str(oid) for oid in ext.value]
    
    return info


def verify_certificate(cert: x509.Certificate, ca_cert: x509.Certificate) -> bool:
    """Verify a certificate against a CA certificate.
    
    Args:
        cert: Certificate to verify
        ca_cert: CA certificate
        
    Returns:
        True if verification succeeds
    """
    try:
        # Create a temporary store
        from cryptography.hazmat.cryptography.verification import verify_certificate_signature
        verify_certificate_signature(cert, ca_cert.public_key())
        return True
    except Exception:
        return False


def get_name_string(name: x509.Name) -> str:
    """Convert X.509 Name to a readable string.
    
    Args:
        name: X.509 Name object
        
    Returns:
        String representation
    """
    parts = []
    for attr in name:
        parts.append(f"{attr.oid._name}={attr.value}")
    return ", ".join(parts)


def cert_to_dict(cert: x509.Certificate) -> Dict[str, Any]:
    """Convert certificate to dictionary.
    
    Args:
        cert: Certificate object
        
    Returns:
        Dictionary with certificate data
    """
    result = {
        'subject': get_name_string(cert.subject),
        'issuer': get_name_string(cert.issuer),
        'serial_number': str(cert.serial_number),
        'not_before': cert.not_valid_before_utc.isoformat(),
        'not_after': cert.not_valid_after_utc.isoformat(),
        'is_ca': False,
        'san': [],
    }
    
    for ext in cert.extensions:
        if isinstance(ext, x509.BasicConstraints):
            result['is_ca'] = ext.ca
        elif isinstance(ext, x509.SubjectAlternativeName):
            result['san'] = [str(name) for name in ext.value]
    
    return result
