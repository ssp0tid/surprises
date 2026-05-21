"""Database models and operations for shell-script-hub."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Script(Base):
    """Script model representing a saved shell script."""

    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(default=None)
    content: Mapped[str]  # The script content/template
    tags: Mapped[str] = mapped_column(default="")  # Comma-separated tags
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_tags_list(self) -> list[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class ExecutionHistory(Base):
    """Execution history model logging script runs."""

    __tablename__ = "execution_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(index=True)
    script_name: Mapped[str]
    variables_used: Mapped[Optional[str]] = mapped_column(default=None)  # JSON
    exit_code: Mapped[Optional[int]]
    output: Mapped[Optional[str]] = mapped_column(default=None)
    error: Mapped[Optional[str]] = mapped_column(default=None)
    executed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "script_id": self.script_id,
            "script_name": self.script_name,
            "variables_used": self.variables_used,
            "exit_code": self.exit_code,
            "output": self.output,
            "error": self.error,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class Database:
    """Database manager for shell-script-hub."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database with optional path."""
        if db_path is None:
            db_path = Path.cwd() / ".shell_script_hub" / "scripts.db"

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        Base.metadata.create_all(self.engine)

    def create_script(
        self,
        name: str,
        content: str,
        description: Optional[str] = None,
        tags: str = "",
    ) -> Script:
        """Create a new script in the database."""
        with Session(self.engine) as session:
            # Check if script with same name exists
            existing = session.execute(
                select(Script).where(Script.name == name)
            ).scalar_one_or_none()

            if existing:
                raise ValueError(f"Script '{name}' already exists")

            script = Script(
                name=name,
                content=content,
                description=description,
                tags=tags,
            )
            session.add(script)
            session.commit()
            session.refresh(script)
            return script

    def update_script(
        self,
        name: str,
        content: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Script:
        """Update an existing script."""
        with Session(self.engine) as session:
            script = session.execute(select(Script).where(Script.name == name)).scalar_one_or_none()

            if not script:
                raise ValueError(f"Script '{name}' not found")

            if content is not None:
                script.content = content
            if description is not None:
                script.description = description
            if tags is not None:
                script.tags = tags

            script.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(script)
            return script

    def get_script(self, name: str) -> Optional[Script]:
        """Get a script by name."""
        with Session(self.engine) as session:
            return session.execute(select(Script).where(Script.name == name)).scalar_one_or_none()

    def list_scripts(
        self,
        tag: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> list[Script]:
        """List all scripts with optional filtering."""
        with Session(self.engine) as session:
            query = select(Script)

            if tag:
                # Filter by tag (contains in comma-separated list)
                query = query.where(Script.tags.contains(tag))

            if search_query:
                query = query.where(
                    (Script.name.contains(search_query))
                    | (Script.description.contains(search_query))
                    | (Script.content.contains(search_query))
                )

            return list(session.execute(query.order_by(Script.name)).scalars().all())

    def delete_script(self, name: str) -> bool:
        """Delete a script by name."""
        with Session(self.engine) as session:
            script = session.execute(select(Script).where(Script.name == name)).scalar_one_or_none()

            if not script:
                return False

            session.delete(script)
            session.commit()
            return True

    def add_execution(
        self,
        script_id: int,
        script_name: str,
        variables_used: Optional[str] = None,
        exit_code: Optional[int] = None,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ExecutionHistory:
        """Add execution history entry."""
        with Session(self.engine) as session:
            history = ExecutionHistory(
                script_id=script_id,
                script_name=script_name,
                variables_used=variables_used,
                exit_code=exit_code,
                output=output,
                error=error,
            )
            session.add(history)
            session.commit()
            session.refresh(history)
            return history

    def get_history(
        self,
        script_name: Optional[str] = None,
        limit: int = 50,
    ) -> list[ExecutionHistory]:
        """Get execution history."""
        with Session(self.engine) as session:
            query = select(ExecutionHistory)

            if script_name:
                query = query.where(ExecutionHistory.script_name == script_name)

            return list(
                session.execute(query.order_by(ExecutionHistory.executed_at.desc()).limit(limit))
                .scalars()
                .all()
            )
