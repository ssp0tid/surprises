"""
Database models for Incident Command Center.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from enum import Enum


class Base(DeclarativeBase):
    pass


class Severity(Enum):
    P1 = "P1"  # Critical - Production down
    P2 = "P2"  # High - Major feature broken
    P3 = "P3"  # Medium - Minor feature broken
    P4 = "P4"  # Low - Cosmetic/minor issue


class IncidentStatus(Enum):
    DECLARED = "Declared"
    INVESTIGATING = "Investigating"
    IDENTIFIED = "Identified"
    MITIGATING = "Mitigating"
    RESOLVED = "Resolved"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(2), nullable=False, default="P3")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Declared")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    timeline: Mapped[list["TimelineEntry"]] = relationship(back_populates="incident", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class TimelineEntry(Base):
    __tablename__ = "timeline_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(Integer, ForeignKey("incidents.id"), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)  # status_change, note, assignment
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    incident: Mapped["Incident"] = relationship(back_populates="timeline")

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "entry_type": self.entry_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


class OnCallEngineer(Base):
    __tablename__ = "on_call_engineers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # primary, secondary, escalation
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": bool(self.is_active),
        }


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(Integer, ForeignKey("incidents.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "content": self.content,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Database:
    def __init__(self, db_path: str = "incidents.db"):
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        return self.async_session()
