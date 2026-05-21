"""
Storage layer for MailCatcher.

Handles SQLite database operations and EML file storage.
"""

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "mailcatcher.db"
EMAILS_DIR = DATA_DIR / "emails"

# Database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Session:
    """
    Get database session with proper cleanup.

    Yields:
        Session: SQLAlchemy session

    Raises:
        Exception: Any database error
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database and create tables.

    Creates:
        - data/ directory if not exists
        - data/emails/ directory if not exists
        - emails table with indexes

    Raises:
        Exception: If database initialization fails
    """
    try:
        # Ensure directories exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        EMAILS_DIR.mkdir(parents=True, exist_ok=True)

        # Create tables
        Base.metadata.create_all(engine)

        # Create indexes separately for compatibility
        with engine.connect() as conn:
            # idx_emails_received_at
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at DESC)"
            )
            # idx_emails_sender
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)"
            )
            conn.commit()

        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def save_email(email_data: dict) -> int:
    """
    Save email to database.

    Args:
        email_data: Dictionary containing email fields

    Returns:
        int: Saved email ID

    Raises:
        Exception: If save fails
    """
    try:
        with get_session() as session:
            recipients_json = json.dumps(email_data.get("recipients", []))
            headers_json = json.dumps(email_data.get("headers", {}))

            email = Email(
                message_id=email_data.get("message_id"),
                subject=email_data.get("subject"),
                sender=email_data.get("sender"),
                recipients=recipients_json,
                date=email_data.get("date"),
                text_body=email_data.get("text_body"),
                html_body=email_data.get("html_body"),
                headers=headers_json,
                has_attachments=email_data.get("has_attachments", False),
                eml_filename=email_data.get("eml_filename"),
            )

            session.add(email)
            session.flush()
            email_id = email.id
            logger.info(f"Saved email id={email_id}, message_id={email.message_id}")
            return email_id
    except Exception as e:
        logger.error(f"Failed to save email: {e}")
        raise


def get_email(email_id: int) -> Optional[Email]:
    """
    Get single email by ID.

    Args:
        email_id: Email primary key

    Returns:
        Optional[Email]: Email object if found, None otherwise
    """
    try:
        with get_session() as session:
            email = session.get(Email, email_id)
            return email
    except Exception as e:
        logger.error(f"Failed to get email {email_id}: {e}")
        return None


def get_emails(
    page: int = 1,
    per_page: int = 20,
    subject: Optional[str] = None,
    sender: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> list[Email]:
    """
    Get paginated list of emails with optional filters.

    Args:
        page: Page number (1-indexed)
        per_page: Number of items per page
        subject: Filter by subject (partial match)
        sender: Filter by sender (partial match)
        date_from: Filter by received_at >= date_from
        date_to: Filter by received_at <= date_to

    Returns:
        list[Email]: List of Email objects
    """
    try:
        with get_session() as session:
            stmt = select(Email).order_by(Email.received_at.desc())

            # Apply filters
            if subject:
                stmt = stmt.where(Email.subject.contains(subject))
            if sender:
                stmt = stmt.where(Email.sender.contains(sender))
            if date_from:
                stmt = stmt.where(Email.received_at >= date_from)
            if date_to:
                stmt = stmt.where(Email.received_at <= date_to)

            # Pagination
            offset = (page - 1) * per_page
            stmt = stmt.offset(offset).limit(per_page)

            result = session.execute(stmt)
            emails = list(result.scalars().all())
            return emails
    except Exception as e:
        logger.error(f"Failed to get emails: {e}")
        return []


def delete_email(email_id: int) -> bool:
    """
    Delete email and its EML file.

    Args:
        email_id: Email primary key

    Returns:
        bool: True if deleted, False if not found
    """
    try:
        with get_session() as session:
            email = session.get(Email, email_id)
            if not email:
                logger.warning(f"Email {email_id} not found")
                return False

            # Delete EML file if exists
            if email.eml_filename:
                eml_path = EMAILS_DIR / email.eml_filename
                try:
                    if eml_path.exists():
                        eml_path.unlink()
                        logger.info(f"Deleted EML file: {eml_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete EML file: {e}")

            session.delete(email)
            session.flush()
            logger.info(f"Deleted email id={email_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to delete email {email_id}: {e}")
        return False


def delete_emails(email_ids: list[int]) -> int:
    """
    Bulk delete emails.

    Args:
        email_ids: List of email IDs to delete

    Returns:
        int: Number of emails deleted
    """
    deleted_count = 0
    for email_id in email_ids:
        if delete_email(email_id):
            deleted_count += 1
    return deleted_count


def clear_all_emails() -> int:
    """
    Delete all emails from database and EML files.

    Returns:
        int: Number of emails deleted
    """
    try:
        with get_session() as session:
            # Get all emails
            stmt = select(Email)
            result = session.execute(stmt)
            emails = list(result.scalars().all())
            count = len(emails)

            # Delete all EML files
            for email in emails:
                if email.eml_filename:
                    eml_path = EMAILS_DIR / email.eml_filename
                    try:
                        if eml_path.exists():
                            eml_path.unlink()
                    except OSError as e:
                        logger.warning(f"Failed to delete EML file: {e}")

            # Delete all emails
            for email in emails:
                session.delete(email)

            session.flush()
            logger.info(f"Cleared all emails: {count} deleted")
            return count
    except Exception as e:
        logger.error(f"Failed to clear emails: {e}")
        return 0


def search_emails(query: str) -> list[Email]:
    """
    Search emails by subject or sender.

    Args:
        query: Search query string

    Returns:
        list[Email]: Matching Email objects
    """
    try:
        with get_session() as session:
            stmt = select(Email).order_by(Email.received_at.desc())

            # Search in subject or sender
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                (Email.subject.contains(search_pattern))
                | (Email.sender.contains(search_pattern))
            )

            result = session.execute(stmt)
            emails = list(result.scalars().all())
            logger.info(f'Search "{query}" returned {len(emails)} results')
            return emails
    except Exception as e:
        logger.error(f"Failed to search emails: {e}")
        return []
