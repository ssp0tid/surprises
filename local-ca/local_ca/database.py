"""Database layer for local-ca."""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from . import crypto_utils
from cryptography import x509


DATABASE_PATH = Path(__file__).parent.parent / "data" / "local-ca.db"
CERTS_DIR = Path(__file__).parent.parent / "data" / "certs"


def init_database() -> None:
    """Initialize the database and create tables."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CERTS_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # Create CAs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('root', 'intermediate')),
            parent_id INTEGER REFERENCES cas(id),
            serial_number TEXT NOT NULL,
            subject TEXT NOT NULL,
            issuer TEXT NOT NULL,
            not_before INTEGER NOT NULL,
            not_after INTEGER NOT NULL,
            key_usage TEXT,
            is_ca INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            cert_path TEXT,
            key_path TEXT
        )
    ''')
    
    # Create certificates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ca_id INTEGER NOT NULL REFERENCES cas(id),
            name TEXT NOT NULL,
            common_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            serial_number TEXT NOT NULL,
            not_before INTEGER NOT NULL,
            not_after INTEGER NOT NULL,
            key_usage TEXT,
            san TEXT,
            created_at INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            cert_path TEXT,
            key_path TEXT
        )
    ''')
    
    # Create CSRs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS csrs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            csr_data TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    return sqlite3.connect(str(DATABASE_PATH))


def _row_to_ca(row: Tuple) -> Dict[str, Any]:
    """Convert database row to CA dictionary."""
    return {
        'id': row[0],
        'name': row[1],
        'type': row[2],
        'parent_id': row[3],
        'serial_number': row[4],
        'subject': row[5],
        'issuer': row[6],
        'not_before': datetime.fromtimestamp(row[7]),
        'not_after': datetime.fromtimestamp(row[8]),
        'key_usage': row[9],
        'is_ca': bool(row[10]),
        'created_at': datetime.fromtimestamp(row[11]),
        'updated_at': datetime.fromtimestamp(row[12]),
        'is_active': bool(row[13]),
        'cert_path': row[14],
        'key_path': row[15],
    }


def _row_to_cert(row: Tuple) -> Dict[str, Any]:
    """Convert database row to certificate dictionary."""
    return {
        'id': row[0],
        'ca_id': row[1],
        'name': row[2],
        'common_name': row[3],
        'subject': row[4],
        'serial_number': row[5],
        'not_before': datetime.fromtimestamp(row[6]),
        'not_after': datetime.fromtimestamp(row[7]),
        'key_usage': row[8],
        'san': json.loads(row[9]) if row[9] else [],
        'created_at': datetime.fromtimestamp(row[10]),
        'is_active': bool(row[11]),
        'cert_path': row[12],
        'key_path': row[13],
    }


def _row_to_csr(row: Tuple) -> Dict[str, Any]:
    """Convert database row to CSR dictionary."""
    return {
        'id': row[0],
        'name': row[1],
        'csr_data': row[2],
        'created_at': datetime.fromtimestamp(row[3]),
    }


# CA Operations
def create_ca(
    name: str,
    ca_type: str,
    subject: str,
    issuer: str,
    not_before: datetime,
    not_after: datetime,
    serial_number: str,
    parent_id: Optional[int] = None,
    is_ca: bool = True,
    cert_path: str = None,
    key_path: str = None
) -> int:
    """Create a new CA in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = int(datetime.now().timestamp())
    
    cursor.execute('''
        INSERT INTO cas (
            name, type, parent_id, serial_number, subject, issuer,
            not_before, not_after, is_ca, created_at, updated_at,
            is_active, cert_path, key_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        name, ca_type, parent_id, serial_number, subject, issuer,
        int(not_before.timestamp()), int(not_after.timestamp()),
        is_ca, now, now, 1, cert_path, key_path
    ))
    
    ca_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return ca_id


def get_ca(ca_id: int) -> Optional[Dict[str, Any]]:
    """Get a CA by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, type, parent_id, serial_number, subject, issuer,
               not_before, not_after, key_usage, is_ca, created_at,
               updated_at, is_active, cert_path, key_path
        FROM cas WHERE id = ?
    ''', (ca_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_ca(row) if row else None


def get_all_cas() -> List[Dict[str, Any]]:
    """Get all CAs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, type, parent_id, serial_number, subject, issuer,
               not_before, not_after, key_usage, is_ca, created_at,
               updated_at, is_active, cert_path, key_path
        FROM cas ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_ca(row) for row in rows]


def get_root_cas() -> List[Dict[str, Any]]:
    """Get all root CAs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, type, parent_id, serial_number, subject, issuer,
               not_before, not_after, key_usage, is_ca, created_at,
               updated_at, is_active, cert_path, key_path
        FROM cas WHERE type = 'root' ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_ca(row) for row in rows]


def delete_ca(ca_id: int) -> bool:
    """Delete a CA."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM cas WHERE id = ?', (ca_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


# Certificate Operations
def create_certificate(
    ca_id: int,
    name: str,
    common_name: str,
    subject: str,
    serial_number: str,
    not_before: datetime,
    not_after: datetime,
    san: Optional[List[str]] = None,
    cert_path: str = None,
    key_path: str = None
) -> int:
    """Create a new certificate in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = int(datetime.now().timestamp())
    san_json = json.dumps(san) if san else '[]'
    
    cursor.execute('''
        INSERT INTO certificates (
            ca_id, name, common_name, subject, serial_number,
            not_before, not_after, san, created_at, is_active,
            cert_path, key_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ca_id, name, common_name, subject, serial_number,
        int(not_before.timestamp()), int(not_after.timestamp()),
        san_json, now, 1, cert_path, key_path
    ))
    
    cert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return cert_id


def get_certificate(cert_id: int) -> Optional[Dict[str, Any]]:
    """Get a certificate by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, ca_id, name, common_name, subject, serial_number,
               not_before, not_after, key_usage, san, created_at,
               is_active, cert_path, key_path
        FROM certificates WHERE id = ?
    ''', (cert_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_cert(row) if row else None


def get_certificates_by_ca(ca_id: int) -> List[Dict[str, Any]]:
    """Get all certificates issued by a CA."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, ca_id, name, common_name, subject, serial_number,
               not_before, not_after, key_usage, san, created_at,
               is_active, cert_path, key_path
        FROM certificates WHERE ca_id = ? ORDER BY created_at DESC
    ''', (ca_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_cert(row) for row in rows]


def get_all_certificates() -> List[Dict[str, Any]]:
    """Get all certificates."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, ca_id, name, common_name, subject, serial_number,
               not_before, not_after, key_usage, san, created_at,
               is_active, cert_path, key_path
        FROM certificates ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_cert(row) for row in rows]


def delete_certificate(cert_id: int) -> bool:
    """Delete a certificate."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM certificates WHERE id = ?', (cert_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


# CSR Operations
def create_csr(
    name: str,
    csr_data: str
) -> int:
    """Create a new CSR in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = int(datetime.now().timestamp())
    
    cursor.execute('''
        INSERT INTO csrs (name, csr_data, created_at)
        VALUES (?, ?, ?)
    ''', (name, csr_data, now))
    
    csr_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return csr_id


def get_csr(csr_id: int) -> Optional[Dict[str, Any]]:
    """Get a CSR by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, csr_data, created_at
        FROM csrs WHERE id = ?
    ''', (csr_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_csr(row) if row else None


def get_all_csrs() -> List[Dict[str, Any]]:
    """Get all CSRs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, csr_data, created_at
        FROM csrs ORDER BY created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_csr(row) for row in rows]


def delete_csr(csr_id: int) -> bool:
    """Delete a CSR."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM csrs WHERE id = ?', (csr_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


# Utility functions
def check_database_exists() -> bool:
    """Check if the database exists."""
    return DATABASE_PATH.exists()


def get_cert_dir() -> Path:
    """Get the certificates directory."""
    return CERTS_DIR