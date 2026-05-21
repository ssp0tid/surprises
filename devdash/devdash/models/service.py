"""Service data model for discovered dev servers."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Service:
    """Represents a discovered development server."""
    
    id: str
    name: str
    pid: int
    port: int
    protocol: str = "http"
    process_type: str = "unknown"
    command: str = ""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    uptime_seconds: int = 0
    status: str = "running"
    log_file: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'pid': self.pid,
            'port': self.port,
            'protocol': self.protocol,
            'process_type': self.process_type,
            'command': self.command,
            'cpu_percent': round(self.cpu_percent, 1),
            'memory_mb': round(self.memory_mb, 1),
            'memory_percent': round(self.memory_percent, 1),
            'uptime_seconds': self.uptime_seconds,
            'status': self.status,
            'log_file': self.log_file,
            'started_at': self.started_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_process(cls, pid: int, port: int, name: str = None, process_type: str = "unknown") -> 'Service':
        """Create Service from a process and port."""
        import psutil
        import os
        
        try:
            proc = psutil.Process(pid)
            cmdline = proc.cmdline() or []
            command = ' '.join(cmdline) if cmdline else ''
            
            if not name:
                # Try to extract name from command
                if process_type == 'node':
                    name = 'Node.js'
                elif process_type == 'python':
                    name = 'Python'
                elif process_type == 'go':
                    name = 'Go'
                else:
                    name = proc.name() or f'Port {port}'
            
            import time
            with proc.oneshot():
                cpu = proc.cpu_percent(interval=0.1)
                mem_info = proc.memory_info()
                memory_mb = mem_info.rss / 1024 / 1024
                create_time = proc.create_time()
                uptime = int(time.time() - create_time)  # Wall clock uptime
            
            return cls(
                id=f"{process_type}-{port}",
                name=name,
                pid=pid,
                port=port,
                process_type=process_type,
                command=command[:200],  # Truncate long commands
                cpu_percent=cpu,
                memory_mb=memory_mb,
                uptime_seconds=int(uptime),
                status='running'
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return cls(
                id=f"unknown-{port}",
                name=name or f'Port {port}',
                pid=pid,
                port=port,
                status='stopped'
            )