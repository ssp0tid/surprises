"""Port scanner module for PortPilot.

Provides functionality to list open ports with process information
and detect port conflicts.
"""

import subprocess
import re
import socket
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class PortInfo:
    """Information about an open port."""
    protocol: str
    local_address: str
    local_port: int
    state: str
    process_name: Optional[str] = None
    process_id: Optional[int] = None


def get_open_ports() -> List[PortInfo]:
    """Get all open ports using ss or netstat.
    
    Returns:
        List of PortInfo objects representing open ports.
    """
    ports = []
    
    # Try ss first (more modern)
    try:
        result = subprocess.run(
            ['ss', '-tuanp'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            ports = _parse_ss_output(result.stdout)
            if ports:
                return ports
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback to netstat
    try:
        result = subprocess.run(
            ['netstat', '-tunp'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return _parse_netstat_output(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Last resort: use /proc filesystem
    return _parse_proc_ports()


def _parse_ss_output(output: str) -> List[PortInfo]:
    """Parse ss command output."""
    ports = []
    lines = output.strip().split('\n')
    
    # Skip header
    for line in lines[1:]:
        if not line.strip():
            continue
        
        parts = line.split()
        if len(parts) < 4:
            continue
        
        try:
            protocol = parts[0].replace('State', '').strip() or parts[0]
            if 'ESTAB' in line:
                state = 'ESTABLISHED'
            elif 'LISTEN' in line:
                state = 'LISTEN'
            elif 'TIME-WAIT' in line:
                state = 'TIME_WAIT'
            elif 'CLOSE-WAIT' in line:
                state = 'CLOSE_WAIT'
            else:
                state = 'UNKNOWN'
            
            # Parse local address
            local = parts[4] if len(parts) > 4 else ''
            if ':' in local:
                addr, port = local.rsplit(':', 1)
                try:
                    local_port = int(port)
                except ValueError:
                    continue
            else:
                continue
            
            # Try to get process info from the last column
            process_name = None
            process_id = None
            if len(parts) > 6 and '(' in parts[-1]:
                proc_part = parts[-1]
                pid_match = re.search(r'pid=(\d+)', proc_part)
                name_match = re.search(r'"([^"]+)"', proc_part)
                if pid_match:
                    process_id = int(pid_match.group(1))
                if name_match:
                    process_name = name_match.group(1)
            
            ports.append(PortInfo(
                protocol=protocol,
                local_address=addr,
                local_port=local_port,
                state=state,
                process_name=process_name,
                process_id=process_id
            ))
        except (ValueError, IndexError):
            continue
    
    return ports


def _parse_netstat_output(output: str) -> List[PortInfo]:
    """Parse netstat command output."""
    ports = []
    lines = output.strip().split('\n')
    
    # Skip header
    for line in lines[2:]:
        if not line.strip():
            continue
        
        parts = line.split()
        if len(parts) < 6:
            continue
        
        try:
            protocol = parts[0]
            local = parts[3]
            
            if ':' not in local:
                continue
            
            addr, port = local.rsplit(':', 1)
            local_port = int(port)
            
            state = parts[5] if len(parts) > 5 else 'UNKNOWN'
            
            # Get process info
            process_name = None
            process_id = None
            if len(parts) > 6:
                proc = parts[6]
                if '/' in proc:
                    proc_parts = proc.split('/')
                    process_id = int(proc_parts[0])
                    process_name = proc_parts[1] if len(proc_parts) > 1 else None
            
            ports.append(PortInfo(
                protocol=protocol,
                local_address=addr,
                local_port=local_port,
                state=state,
                process_name=process_name,
                process_id=process_id
            ))
        except (ValueError, IndexError):
            continue
    
    return ports


def _parse_proc_ports() -> List[PortInfo]:
    """Parse /proc filesystem as last resort."""
    ports = []
    
    try:
        # Read TCP connections
        tcp_ports = _read_inet_diagram('/proc/net/tcp')
        tcp6_ports = _read_inet_diagram('/proc/net/tcp6')
        
        # Read UDP connections
        udp_ports = _read_inet_diagram('/proc/net/udp')
        udp6_ports = _read_inet_diagram('/proc/net/udp6')
        
        all_ports = tcp_ports + tcp6_ports + udp_ports + udp6_ports
        
        # Deduplicate by (address, port)
        seen = set()
        for p in all_ports:
            key = (p.local_address, p.local_port)
            if key not in seen:
                seen.add(key)
                ports.append(p)
        
    except Exception:
        pass
    
    return ports


def _read_inet_diagram(path: str) -> List[PortInfo]:
    """Read port info from /proc/net/* files."""
    ports = []
    
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return ports
    
    protocol = 'TCP' if 'tcp' in path else 'UDP'
    
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 10:
            continue
        
        try:
            local_addr = parts[1]
            local_port = int(local_addr.split(':')[1], 16)
            
            # Convert hex address to dotted notation
            addr_hex = local_addr.split(':')[0]
            addr_int = int(addr_hex, 16)
            addr = socket.inet_ntoa(bytes.fromhex(format(addr_int, '08x')))
            
            state_code = int(parts[3], 16)
            state = _get_tcp_state(state_code)
            
            # Try to get inode and find process
            inode = parts[9]
            process_name, process_id = _find_process_by_inode(inode)
            
            ports.append(PortInfo(
                protocol=protocol,
                local_address=addr,
                local_port=local_port,
                state=state,
                process_name=process_name,
                process_id=process_id
            ))
        except (ValueError, IndexError):
            continue
    
    return ports


def _get_tcp_state(code: int) -> str:
    """Map TCP state code to name."""
    states = {
        1: 'ESTABLISHED',
        2: 'SYN_SENT',
        3: 'SYN_RECV',
        4: 'FIN_WAIT1',
        5: 'FIN_WAIT2',
        6: 'TIME_WAIT',
        7: 'CLOSE',
        8: 'CLOSE_WAIT',
        9: 'LAST_ACK',
        10: 'LISTEN',
        11: 'CLOSING',
        12: 'NEW_SYN_RECV',
    }
    return states.get(code, 'UNKNOWN')


def _find_process_by_inode(inode: str) -> Tuple[Optional[str], Optional[int]]:
    """Find process that owns a socket inode."""
    if not inode or inode == '0':
        return None, None
    
    try:
        for pid_dir in range(1, 32768):
            try:
                fd_path = f'/proc/{pid_dir}/fd'
                if not fd_path:
                    continue
                for fd in range(0, 256):
                    try:
                        link = f'/proc/{pid_dir}/fd/{fd}'
                        result = subprocess.run(
                            ['readlink', link],
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        if result.returncode == 0 and f'socket:[{inode}]' in result.stdout:
                            # Found it, get process name
                            with open(f'/proc/{pid_dir}/comm', 'r') as f:
                                name = f.read().strip()
                            return name, pid_dir
                    except (FileNotFoundError, ProcessLookupError):
                        continue
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
    except Exception:
        pass
    
    return None, None


def detect_port_conflicts(ports: List[PortInfo]) -> List[Tuple[PortInfo, PortInfo]]:
    """Detect port conflicts (same port used by multiple processes).
    
    Args:
        ports: List of open ports.
        
    Returns:
        List of tuples containing pairs of conflicting ports.
    """
    by_port = {}
    conflicts = []
    
    for port in ports:
        key = (port.local_address, port.local_port)
        if key in by_port:
            conflicts.append((by_port[key], port))
        else:
            by_port[key] = port
    
    return conflicts


def check_port_available(port: int, host: str = '0.0.0.0') -> bool:
    """Check if a port is available (not in use).
    
    Args:
        port: Port number to check.
        host: Host address to check (default: all interfaces).
        
    Returns:
        True if port is available, False if in use.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False


def find_available_port(start: int = 8000, end: int = 9000) -> Optional[int]:
    """Find an available port in the given range.
    
    Args:
        start: Starting port number (default: 8000).
        end: Ending port number (default: 9000).
        
    Returns:
        Available port number, or None if no ports available.
    """
    for port in range(start, end + 1):
        if check_port_available(port):
            return port
    return None