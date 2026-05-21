"""Service discovery - scans for dev servers on localhost ports."""

import socket
import psutil
from typing import List, Optional
from ..models.service import Service


# Common dev server port ranges
DEFAULT_PORTS = list(range(3000, 9001))

# Process type detection patterns
PROCESS_PATTERNS = {
    'node': ['node', 'npm', 'npx', 'bun', 'deno'],
    'python': ['python', 'python3', 'flask', 'fastapi', 'uvicorn', 'django', 'gunicorn'],
    'go': ['go run', 'go build', '/go-build'],
    'java': ['java', 'gradle', 'maven'],
    'ruby': ['ruby', 'rails', 'bundle'],
    'php': ['php', 'composer', 'artisan'],
}


class ServiceDiscoverer:
    """Discovers development servers running on localhost ports."""
    
    def __init__(self, scan_ports: List[int] = None):
        self.scan_ports = scan_ports or DEFAULT_PORTS
        self.blacklist = [
            'chrome', 'firefox', 'slack', 'vscode', 'code',
            'electron', 'spotify', 'discord', 'skype'
        ]
    
    def discover(self) -> List[Service]:
        """Scan for all development server processes."""
        services = []
        seen_ports = set()
        
        # First, scan all ports to find which are in use
        port_to_pid = self._scan_ports()
        
        # Now, map each port to a process and create Service
        for port, pid in port_to_pid.items():
            if port in seen_ports:
                continue
            seen_ports.add(port)
            
            try:
                proc = psutil.Process(pid)
                proc_name = proc.name().lower()
                
                # Skip blacklisted processes
                if any(bl in proc_name for bl in self.blacklist):
                    continue
                
                # Detect process type
                process_type = self._detect_process_type(proc)
                
                if process_type:
                    service = Service.from_process(
                        pid=pid,
                        port=port,
                        process_type=process_type
                    )
                    # Update memory percent
                    try:
                        service.memory_percent = proc.memory_percent()
                    except Exception:
                        pass
                    services.append(service)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return services
    
    def _scan_ports(self) -> dict:
        """Scan ports to find which are listening."""
        port_to_pid = {}
        
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr:
                port = conn.laddr.port
                if port in self.scan_ports:
                    # Prefer lower PIDs (usually the main process)
                    if port not in port_to_pid or conn.pid < port_to_pid[port]:
                        if conn.pid:
                            port_to_pid[port] = conn.pid
        
        return port_to_pid
    
    def _detect_process_type(self, proc: psutil.Process) -> Optional[str]:
        """Detect the type of dev server from process info."""
        try:
            cmdline = proc.cmdline() or []
            command = ' '.join(cmdline).lower()
            name = proc.name().lower()
            
            # Check patterns
            for ptype, patterns in PROCESS_PATTERNS.items():
                for pattern in patterns:
                    if pattern in command or pattern in name:
                        return ptype
            
            # Check for common dev server indicators
            if 'vite' in command or 'webpack' in command or 'webpack-dev-server' in command:
                return 'node'
            if 'react' in command or 'vue' in command or 'angular' in command:
                return 'node'
            
            return None
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def get_service_by_port(self, port: int) -> Optional[Service]:
        """Find a service on a specific port."""
        services = self.discover()
        for service in services:
            if service.port == port:
                return service
        return None