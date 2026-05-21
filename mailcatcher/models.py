"""
Email model for MailCatcher.

Defines the Email class using SQLAlchemy declarative base.
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class."""

    pass


class Email(Base):
    """
    Email model representing captured emails.

    Attributes:
        id: Primary key
        message_id: Unique message ID from email headers
        subject: Email subject line
        sender: From address
        recipients: JSON array of recipient addresses
        date: Date from email headers (parsed)
        received_at: Timestamp when email was received
        text_body: Plain text body
        html_body: HTML body
        headers: JSON object of email headers
        has_attachments: Boolean flag for attachments
        eml_filename: Filename of stored EML file
    """

    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sender: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    recipients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default=datetime.utcnow
    )
    text_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object
    has_attachments: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    eml_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Email(id={self.id}, subject={self.subject!r}, sender={self.sender!r})>"
        )

    def get_recipients(self) -> list[str]:
        """Parse recipients JSON array."""
        if not self.recipients:
            return []
        try:
            return json.loads(self.recipients)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_headers(self) -> dict:
        """Parse headers JSON object."""
        if not self.headers:
            return {}
        try:
            return json.loads(self.headers)
        except (json.JSONDecodeError, TypeError):
            return {}
