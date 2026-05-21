"""
Database operations for Incident Command Center.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models import Database, Incident, TimelineEntry, OnCallEngineer, IncidentStatus


class IncidentManager:
    def __init__(self, db: Database):
        self.db = db

    async def create_incident(
        self,
        title: str,
        description: str = "",
        severity: str = "P3",
        assigned_to: Optional[str] = None
    ) -> Incident:
        async with self.db.async_session() as session:
            incident = Incident(
                title=title,
                description=description,
                severity=severity,
                status=IncidentStatus.DECLARED.value,
                assigned_to=assigned_to
            )
            session.add(incident)
            await session.commit()
            await session.refresh(incident)

            # Add timeline entry for creation
            entry = TimelineEntry(
                incident_id=incident.id,
                entry_type="status_change",
                content=f"Incident declared with severity {severity}",
            )
            session.add(entry)
            await session.commit()

            return incident

    async def get_incident(self, incident_id: int) -> Optional[Incident]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            return result.scalar_one_or_none()

    async def get_all_incidents(self) -> list[Incident]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).order_by(Incident.created_at.desc())
            )
            return list(result.scalars().all())

    async def update_status(self, incident_id: int, new_status: str, updated_by: Optional[str] = None) -> Optional[Incident]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            incident = result.scalar_one_or_none()
            if not incident:
                return None

            old_status = incident.status
            incident.status = new_status
            incident.updated_at = datetime.utcnow()

            if new_status == IncidentStatus.RESOLVED.value:
                incident.resolved_at = datetime.utcnow()

            # Add timeline entry
            entry = TimelineEntry(
                incident_id=incident_id,
                entry_type="status_change",
                content=f"Status changed from {old_status} to {new_status}",
                created_by=updated_by
            )
            session.add(entry)
            await session.commit()
            await session.refresh(incident)
            return incident

    async def assign_incident(self, incident_id: int, assignee: str, assigned_by: Optional[str] = None) -> Optional[Incident]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            incident = result.scalar_one_or_none()
            if not incident:
                return None

            old_assignee = incident.assigned_to
            incident.assigned_to = assignee
            incident.updated_at = datetime.utcnow()

            # Add timeline entry
            content = f"Assigned to {assignee}"
            if old_assignee:
                content = f"Reassigned from {old_assignee} to {assignee}"
            entry = TimelineEntry(
                incident_id=incident_id,
                entry_type="assignment",
                content=content,
                created_by=assigned_by
            )
            session.add(entry)
            await session.commit()
            await session.refresh(incident)
            return incident

    async def update_severity(self, incident_id: int, severity: str, updated_by: Optional[str] = None) -> Optional[Incident]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            incident = result.scalar_one_or_none()
            if not incident:
                return None

            old_severity = incident.severity
            incident.severity = severity
            incident.updated_at = datetime.utcnow()

            # Add timeline entry
            entry = TimelineEntry(
                incident_id=incident_id,
                entry_type="status_change",
                content=f"Severity changed from {old_severity} to {severity}",
                created_by=updated_by
            )
            session.add(entry)
            await session.commit()
            await session.refresh(incident)
            return incident

    async def delete_incident(self, incident_id: int) -> bool:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            incident = result.scalar_one_or_none()
            if not incident:
                return False
            await session.delete(incident)
            await session.commit()
            return True


class TimelineManager:
    def __init__(self, db: Database):
        self.db = db

    async def add_note(self, incident_id: int, content: str, author: Optional[str] = None) -> Optional[TimelineEntry]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            incident = result.scalar_one_or_none()
            if not incident:
                return None

            entry = TimelineEntry(
                incident_id=incident_id,
                entry_type="note",
                content=content,
                created_by=author
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

    async def get_timeline(self, incident_id: int) -> list[TimelineEntry]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(TimelineEntry)
                .where(TimelineEntry.incident_id == incident_id)
                .order_by(TimelineEntry.created_at.desc())
            )
            return list(result.scalars().all())


class OnCallManager:
    def __init__(self, db: Database):
        self.db = db

    async def add_engineer(self, name: str, email: str, role: str = "secondary") -> OnCallEngineer:
        async with self.db.async_session() as session:
            engineer = OnCallEngineer(
                name=name,
                email=email,
                role=role,
                is_active=True
            )
            session.add(engineer)
            await session.commit()
            await session.refresh(engineer)
            return engineer

    async def get_all_engineers(self) -> list[OnCallEngineer]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(OnCallEngineer).order_by(OnCallEngineer.role, OnCallEngineer.name)
            )
            return list(result.scalars().all())

    async def get_active_engineers(self) -> list[OnCallEngineer]:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(OnCallEngineer)
                .where(OnCallEngineer.is_active == True)
                .order_by(OnCallEngineer.role, OnCallEngineer.name)
            )
            return list(result.scalars().all())

    async def remove_engineer(self, engineer_id: int) -> bool:
        async with self.db.async_session() as session:
            result = await session.execute(
                select(OnCallEngineer).where(OnCallEngineer.id == engineer_id)
            )
            engineer = result.scalar_one_or_none()
            if not engineer:
                return False
            await session.delete(engineer)
            await session.commit()
            return True

    async def seed_default_engineers(self):
        """Seed the database with default on-call engineers."""
        async with self.db.async_session() as session:
            result = await session.execute(select(OnCallEngineer))
            if result.scalars().first() is None:
                default_engineers = [
                    OnCallEngineer(name="Alice Chen", email="alice@company.com", role="primary"),
                    OnCallEngineer(name="Bob Smith", email="bob@company.com", role="secondary"),
                    OnCallEngineer(name="Carol Davis", email="carol@company.com", role="secondary"),
                    OnCallEngineer(name="Dave Wilson", email="dave@company.com", role="escalation"),
                ]
                for eng in default_engineers:
                    session.add(eng)
                await session.commit()
