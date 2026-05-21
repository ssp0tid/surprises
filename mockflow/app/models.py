"""Database models for MockFlow."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    JSON,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

db = SQLAlchemy()


class Project(db.Model):
    """Project model - workspace for organizing endpoints."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    base_url = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    settings = Column(JSON, default=dict)

    endpoints = relationship(
        "Endpoint", back_populates="project", cascade="all, delete-orphan"
    )
    logs = relationship("Log", back_populates="project", cascade="all, delete-orphan")
    server_config = relationship(
        "ServerConfig",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "base_url": self.base_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "settings": self.settings,
            "endpoint_count": len(self.endpoints),
        }


class Endpoint(db.Model):
    """Endpoint model - defines a mock API route."""

    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    description = Column(Text, default="")
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    match_headers = Column(JSON, default=None)
    match_body = Column(JSON, default=None)
    match_query = Column(JSON, default=None)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="endpoints")
    responses = relationship(
        "Response", back_populates="endpoint", cascade="all, delete-orphan"
    )
    logs = relationship("Log", back_populates="endpoint", cascade="all, delete-orphan")

    def to_dict(self, include_responses=False):
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "path": self.path,
            "method": self.method,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
            "match_headers": self.match_headers,
            "match_body": self.match_body,
            "match_query": self.match_query,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_responses:
            result["responses"] = [r.to_dict() for r in self.responses]
        return result


class Response(db.Model):
    """Response model - defines response for an endpoint."""

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    endpoint_id = Column(
        Integer, ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    status_code = Column(Integer, default=200)
    headers = Column(JSON, default=dict)
    body = Column(Text, default="")
    content_type = Column(Text, default="application/json")
    delay_ms = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    conditions = Column(JSON, default=None)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    endpoint = relationship("Endpoint", back_populates="responses")

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "name": self.name,
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "content_type": self.content_type,
            "delay_ms": self.delay_ms,
            "is_default": self.is_default,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Log(db.Model):
    """Log model - request/response history."""

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    endpoint_id = Column(
        Integer, ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
    )
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    method = Column(String(10), nullable=False)
    path = Column(Text, nullable=False)
    query_params = Column(JSON, default=None)
    request_headers = Column(JSON, default=None)
    request_body = Column(Text, default="")
    response_status = Column(Integer, default=0)
    response_headers = Column(JSON, default=None)
    response_body = Column(Text, default="")
    matched = Column(Boolean, default=False)
    response_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    project = relationship("Project", back_populates="logs")
    endpoint = relationship("Endpoint", back_populates="logs")

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "project_id": self.project_id,
            "method": self.method,
            "path": self.path,
            "query_params": self.query_params,
            "request_headers": self.request_headers,
            "request_body": self.request_body,
            "response_status": self.response_status,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
            "matched": self.matched,
            "response_time_ms": self.response_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ServerConfig(db.Model):
    """Server configuration model."""

    __tablename__ = "server_config"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    port = Column(Integer, default=8080)
    host = Column(Text, default="0.0.0.0")
    enabled = Column(Boolean, default=False)
    cors_enabled = Column(Boolean, default=True)
    cors_origins = Column(Text, default="*")
    log_requests = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="server_config")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "port": self.port,
            "host": self.host,
            "enabled": self.enabled,
            "cors_enabled": self.cors_enabled,
            "cors_origins": self.cors_origins,
            "log_requests": self.log_requests,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
