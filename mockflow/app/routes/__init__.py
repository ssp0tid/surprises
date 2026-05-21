"""Routes package initialization."""

from .projects import projects_bp
from .endpoints import endpoints_bp
from .responses import responses_bp
from .logs import logs_bp
from .server import server_bp

__all__ = ["projects_bp", "endpoints_bp", "responses_bp", "logs_bp", "server_bp"]
