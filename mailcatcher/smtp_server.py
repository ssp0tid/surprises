"""
MailCatcher SMTP Server - Phase 2 Implementation
Handles incoming emails using aiosmtpd and stores them in the database.
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.generator import BytesGenerator
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, SMTP, Envelope, Session

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directory configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "mailcatcher.db")
EMAILS_DIR = os.path.join(DATA_DIR, "emails")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EMAILS_DIR, exist_ok=True)

# Important headers to collect
IMPORTANT_HEADERS = [
    "Message-ID",
    "Subject",
    "From",
    "To",
    "Cc",
    "Bcc",
    "Date",
    "Reply-To",
    "In-Reply-To",
    "References",
    "MIME-Version",
    "Content-Type",
    "Content-Transfer-Encoding",
]


# ==================== Database Functions ====================


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database schema."""
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            subject TEXT,
            sender TEXT,
            recipients TEXT,
            date TIMESTAMP,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            text_body TEXT,
            html_body TEXT,
            headers TEXT,
            has_attachments INTEGER DEFAULT 0,
            eml_filename TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at DESC)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)")
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def save_email(email_data: dict) -> int:
    """
    Save email data to database.

    Args:
        email_data: Dictionary containing email metadata

    Returns:
        Database row ID
    """
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO emails (
            message_id,
            subject,
            sender,
            recipients,
            date,
            text_body,
            html_body,
            headers,
            has_attachments,
            eml_filename
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            email_data.get("message_id"),
            email_data.get("subject"),
            email_data.get("sender"),
            email_data.get("recipients"),  # JSON string
            email_data.get("date"),
            email_data.get("text_body"),
            email_data.get("html_body"),
            email_data.get("headers"),  # JSON string
            email_data.get("has_attachments", 0),
            email_data.get("eml_filename"),
        ),
    )
    conn.commit()
    email_id = cursor.lastrowid
    conn.close()
    logger.info(f"Email saved with ID: {email_id}")
    return email_id


def save_eml_file(email_id: int, raw_email: bytes) -> str:
    """
    Save raw EML file to disk.

    Args:
        email_id: Database row ID
        raw_email: Raw email bytes

    Returns:
        Filename
    """
    filename = f"{email_id}.eml"
    filepath = os.path.join(EMAILS_DIR, filename)

    try:
        with open(filepath, "wb") as f:
            f.write(raw_email)
        logger.info(f"EML file saved: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save EML file: {e}")
        raise

    return filename


def update_eml_filename(email_id: int, filename: str):
    """Update EML filename in database."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE emails SET eml_filename = ? WHERE id = ?", (filename, email_id)
    )
    conn.commit()
    conn.close()


# ==================== Email Parsing Functions ====================


def extract_message_id(msg: Message) -> Optional[str]:
    """Extract message ID from headers, generate if missing."""
    message_id = msg.get("Message-ID")
    if message_id:
        # Remove angle brackets if present
        return message_id.strip("<>")
    # Generate a new message ID if missing
    return f"<{uuid.uuid4()}@mailcatcher>"


def extract_subject(msg: Message) -> str:
    """Extract and decode subject line."""
    subject = msg.get("Subject", "(No Subject)")
    if subject:
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_parts.append(part)
        subject = "".join(decoded_parts)
    return subject


def extract_sender(msg: Message) -> str:
    """Extract sender from From header."""
    sender = msg.get("From")
    if not sender:
        return "(Unknown Sender)"
    return sender


def extract_recipients(msg: Message) -> list:
    """Extract recipients from To, Cc headers as JSON array."""
    recipients = []

    # Get To header
    to_header = msg.get("To")
    if to_header:
        recipients.append(to_header)

    # Get Cc header
    cc_header = msg.get("Cc")
    if cc_header:
        recipients.append(cc_header)

    return recipients


def extract_date(msg: Message, received_at: datetime) -> Optional[datetime]:
    """Extract date from Date header or use received_at."""
    date_header = msg.get("Date")
    if date_header:
        try:
            return parsedate_to_datetime(date_header)
        except (ValueError, TypeError):
            pass
    return received_at


def extract_body_parts(msg: Message) -> tuple:
    """
    Extract text/plain and text/html body parts from email.

    Returns:
        Tuple of (text_body, html_body)
    """
    text_body = None
    html_body = None

    def walk_payloads(message):
        """Walk through all payload parts."""
        nonlocal text_body, html_body

        if message.is_multipart():
            for part in message.get_payload():
                walk_payloads(part)
        else:
            content_type = message.get("Content-Type", "").lower()
            payload = message.get_payload(decode=True)

            if payload:
                try:
                    body = payload.decode("utf-8", errors="replace")
                except Exception:
                    try:
                        body = payload.decode("latin-1", errors="replace")
                    except Exception:
                        body = str(payload)

                if "text/plain" in content_type and text_body is None:
                    text_body = body
                elif "text/html" in content_type and html_body is None:
                    html_body = body

    walk_payloads(msg)
    return text_body, html_body


def extract_headers(msg: Message) -> dict:
    """Extract important headers as dictionary."""
    headers = {}
    for header_name in IMPORTANT_HEADERS:
        value = msg.get(header_name)
        if value:
            headers[header_name] = value
    return headers


def check_attachments(msg: Message) -> bool:
    """Check if email has attachments."""
    if not msg.is_multipart():
        return False

    # Check for Content-Disposition: attachment
    for part in msg.walk():
        content_disposition = part.get("Content-Disposition", "")
        if "attachment" in content_disposition.lower():
            return True

    return False


def parse_email(raw_email: bytes, received_at: datetime) -> dict:
    """
    Parse raw email bytes into structured dictionary.

    Args:
        raw_email: Raw email bytes
        received_at: Timestamp when email was received

    Returns:
        Dictionary with email metadata
    """
    try:
        # Parse email message
        parser = BytesParser(policy=policy.default)
        msg = parser.parsebytes(raw_email)

        # Extract components
        message_id = extract_message_id(msg)
        subject = extract_subject(msg)
        sender = extract_sender(msg)
        recipients_list = extract_recipients(msg)
        recipients_json = json.dumps(recipients_list)

        date = extract_date(msg, received_at)
        date_str = date.isoformat() if date else received_at.isoformat()

        text_body, html_body = extract_body_parts(msg)
        headers = extract_headers(msg)
        headers_json = json.dumps(headers)
        has_attachments = 1 if check_attachments(msg) else 0

        return {
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "recipients": recipients_json,
            "date": date_str,
            "text_body": text_body,
            "html_body": html_body,
            "headers": headers_json,
            "has_attachments": has_attachments,
            "raw_email": raw_email,
        }

    except Exception as e:
        logger.error(f"Failed to parse email: {e}")
        raise


# ==================== SMTP Controller ====================


class MailCatcherController:
    """
    SMTP Controller for handling incoming emails.

    Accepts all incoming mail and stores it in the database.
    """

    def __init__(self):
        self.logger = logger

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: dict,
    ) -> str:
        """
        Handle RCPT command - accept all recipients.

        Args:
            server: SMTP server instance
            session: SMTP session
            envelope: SMTP envelope
            address: Recipient address
            rcpt_options: RCPT options

        Returns:
            SMTP response code
        """
        envelope.rcpt_tos.append(address)
        self.logger.debug(f"Accepted recipient: {address}")
        return "250 OK"

    async def handle_DATA(
        self, server: SMTP, session: Session, envelope: Envelope
    ) -> str:
        """
        Handle DATA command - process incoming email.

        Args:
            server: SMTP server instance
            session: SMTP session
            envelope: SMTP envelope

        Returns:
            SMTP response code
        """
        received_at = datetime.utcnow()
        raw_email = envelope.content

        try:
            # Parse email
            email_data = parse_email(raw_email, received_at)

            # Get raw email for EML saving
            raw_email_for_save = email_data.pop("raw_email")

            # Save email to database first (to get ID)
            try:
                email_id = save_email(email_data)
            except sqlite3.IntegrityError:
                # Message-ID might already exist, generate new one
                email_data["message_id"] = f"<{uuid.uuid4()}@mailcatcher>"
                email_id = save_email(email_data)
            except Exception as e:
                self.logger.error(f"Database save failed: {e}")
                return "451 Requested action aborted: storage failure"

            # Save EML file
            try:
                filename = save_eml_file(email_id, raw_email_for_save)
                update_eml_filename(email_id, filename)
            except Exception as e:
                self.logger.error(f"EML save failed: {e}")
                # Continue anyway - email is saved in DB

            self.logger.info(
                f"Email accepted: ID={email_id}, "
                f"Subject={email_data.get('subject')}, "
                f"From={email_data.get('sender')}"
            )

            return "250 Message accepted for delivery"

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid email format (JSON): {e}")
            return "501 Invalid email format"
        except Exception as e:
            self.logger.error(f"DATA handler error: {e}")
            return "451 Requested action aborted: processing error"


# ==================== Server Runner ====================


def run_smtp_server(
    hostname: str = "0.0.0.0",
    port: int = 1025,
    ready_callback: Optional[callable] = None,
) -> Controller:
    """
    Run SMTP server.

    Args:
        hostname: Host to bind to
        port: Port to listen on
        ready_callback: Optional callback when server is ready

    Returns:
        Controller instance
    """
    # Initialize database
    init_database()

    # Create controller
    controller = Controller(
        MailCatcherController(),
        hostname=hostname,
        port=port,
        ready_callback=ready_callback,
    )

    # Start server
    controller.start()
    logger.info(f"SMTP server started on {hostname}:{port}")

    return controller


def stop_smtp_server(controller: Controller):
    """
    Stop SMTP server.

    Args:
        controller: Controller instance to stop
    """
    controller.stop()
    logger.info("SMTP server stopped")


# ==================== Entry Point ====================


if __name__ == "__main__":
    import sys

    print("Starting MailCatcher SMTP Server...")
    print(f"Database: {DB_PATH}")
    print(f"EML Directory: {EMAILS_DIR}")

    try:
        controller = run_smtp_server()
        print("SMTP server running on port 1025")
        print("Press Ctrl+C to stop")

        # Keep running
        while True:
            asyncio.run(asyncio.sleep(1))

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_smtp_server(controller)
        print("Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
