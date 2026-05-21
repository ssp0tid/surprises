"""
Service Discovery Modules for ServiceMap
Includes mDNS/DNS-SD discovery and port scanning with service identification.
"""

import asyncio
import socket
import struct
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import os


# Common service names and their typical ports
COMMON_SERVICES = {
    21: 'FTP',
    22: 'SSH',
    23: 'Telnet',
    25: 'SMTP',
    53: 'DNS',
    80: 'HTTP',
    110: 'POP3',
    143: 'IMAP',
    443: 'HTTPS',
    445: 'SMB',
    465: 'SMTPS',
    587: 'SMTP submission',
    993: 'IMAPS',
    995: 'POP3S',
    1433: 'MSSQL',
    1521: 'Oracle DB',
    3306: 'MySQL',
    3389: 'RDP',
    5432: 'PostgreSQL',
    5900: 'VNC',
    6379: 'Redis',
    8080: 'HTTP Proxy',
    8443: 'HTTPS Alt',
    27017: 'MongoDB',
}

# mDNS/Bonjour service types
MDNS_SERVICE_TYPES = [
    '_services._dns-sd._udp.local',
    '_http._tcp.local',
    '_https._tcp.local',
    '_ssh._tcp.local',
    '_ftp._tcp.local',
    '_sftp-ssh._tcp.local',
    '_smb._tcp.local',
    '_afpovertcp._tcp.local',
    '_nfs._tcp.local',
    '_rsp._tcp.local',  # AirPlay
    '_airplay._tcp.local',
    '_homekit._tcp.local',
    '_hap._tcp.local',  # HomeKit Accessory Protocol
    '_printer._tcp.local',
    '_ipp._tcp.local',
    '_pdl-datastream._tcp.local',
    '_axis-video._tcp.local',
    '_squeezecenter._tcp.local',
    '_snapcast._tcp.local',
]


@dataclass
class DiscoveredService:
    """Represents a discovered network service."""
    name: str
    service_type: str
    host: str
    port: int
    protocol: str = 'tcp'
    txt_record: Optional[Dict] = None


class ServiceScanner:
    """mDNS/DNS-SD service discovery scanner."""
    
    def __init__(self):
        self.discovered = []
    
    async def discover_all_services(self, timeout: float = 5.0) -> List[Dict]:
        """Discover all mDNS/Bonjour services on the local network."""
        services = []
        
        # Try using dns-sd (avahi/mDNSResponder) command if available
        services = await self._try_dns_sd_browse(timeout)
        
        if not services:
            # Fallback: try using avahi-browse
            services = await self._try_avahi_browse(timeout)
        
        if not services:
            # Manual mDNS discovery
            services = await self._manual_mdns_discovery(timeout)
        
        return services
    
    async def _try_dns_sd_browse(self, timeout: float) -> List[Dict]:
        """Try using the dns-sd command for service discovery."""
        services = []
        try:
            proc = await asyncio.create_subprocess_exec(
                'dns-sd', '-B', '_services._dns-sd._udp.local',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                await asyncio.wait_for(self._read_dns_sd_output(proc), timeout)
            except asyncio.TimeoutError:
                proc.terminate()
            
            await proc.wait()
        except FileNotFoundError:
            pass
        
        return services
    
    async def _read_dns_sd_output(self, proc):
        """Read and parse dns-sd output."""
        while proc.returncode is None:
            line = await proc.stdout.readline()
            if not line:
                break
            # Parse dns-sd output format
            # Example: "0:09:12.535  Adding query<DNSSDService> for _services._dns-sd._udp.local."
            line = line.decode('utf-8', errors='ignore')
            # Further parsing would extract service types
    
    async def _try_avahi_browse(self, timeout: float) -> List[Dict]:
        """Try using avahi-browse for service discovery."""
        services = []
        try:
            proc = await asyncio.create_subprocess_exec(
                'avahi-browse', '-r', '-a',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(), timeout
                )
                for line in stdout.decode('utf-8', errors='ignore').split('\n'):
                    if '=' in line:
                        parts = line.split('=')
                        if len(parts) >= 2:
                            services.append({
                                'name': parts[0].strip(),
                                'type': parts[1].strip(),
                                'host': '',
                                'port': 0
                            })
            except asyncio.TimeoutError:
                proc.terminate()
                await proc.wait()
        except FileNotFoundError:
            pass
        
        return services
    
    async def _manual_mdns_discovery(self, timeout: float) -> List[Dict]:
        """Manual mDNS service discovery using raw packets or socket queries."""
        services = []
        
        # Get local IP to determine subnet
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            subnet = '.'.join(local_ip.split('.')[:3])
        except socket.gaierror:
            subnet = '192.168.1'
        
        # Try common service discovery on common local IPs
        # In a real implementation, this would send mDNS queries
        # For now, we simulate with known common services
        
        # Add simulated local network services
        # In production, replace with actual mDNS queries
        services.extend([
            {
                'name': 'ServiceMap.local',
                'type': 'mDNS',
                'host': local_ip,
                'port': 0,
                'protocol': 'udp'
            }
        ])
        
        return services
    
    async def query_service(self, service_type: str, timeout: float = 3.0) -> List[Dict]:
        """Query for a specific service type."""
        services = []
        
        try:
            # Use resolve or avahi-resolve if available
            proc = await asyncio.create_subprocess_exec(
                'avahi-resolve', '--service', service_type,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(), timeout
                )
                for line in stdout.decode('utf-8', errors='ignore').split('\n'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        services.append({
                            'name': parts[0],
                            'type': service_type,
                            'host': parts[1].split(':')[0] if ':' in parts[1] else parts[1],
                            'port': int(parts[1].split(':')[2]) if len(parts[1].split(':')) > 2 else 0
                        })
            except asyncio.TimeoutError:
                proc.terminate()
                await proc.wait()
        except FileNotFoundError:
            pass
        
        return services


class PortScanner:
    """TCP/UDP port scanner with service identification."""
    
    def __init__(self):
        self.timeout = 1.0
    
    def scan_host(self, host: str, start_port: int = 1, end_port: int = 1024) -> List[Tuple[int, str]]:
        """Scan a host for open ports."""
        open_ports = []
        
        # Scan selected ports
        for port in range(start_port, end_port + 1):
            if self._is_port_open(host, port):
                service = COMMON_SERVICES.get(port, 'unknown')
                open_ports.append((port, service))
        
        return open_ports
    
    def scan_host_fast(self, host: str, ports: List[int] = None) -> List[Tuple[int, str]]:
        """Fast scan using concurrent connections."""
        if ports is None:
            # Default common ports
            ports = list(COMMON_SERVICES.keys())
        
        open_ports = []
        
        # Use asyncio for concurrent scanning
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            open_ports = loop.run_until_complete(
                self._async_scan_ports(host, ports)
            )
        finally:
            loop.close()
        
        return open_ports
    
    async def _async_scan_ports(self, host: str, ports: List[int]) -> List[Tuple[int, str]]:
        """Async concurrent port scanning."""
        open_ports = []
        
        async def check_port(port):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=self.timeout
                )
                writer.close()
                await writer.wait_closed()
                return (port, COMMON_SERVICES.get(port, 'unknown'))
            except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
                return None
        
        results = await asyncio.gather(
            *[check_port(p) for p in ports],
            return_exceptions=True
        )
        
        for result in results:
            if result is not None and not isinstance(result, Exception):
                open_ports.append(result)
        
        return open_ports
    
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if a single port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except (socket.error, OSError):
            return False
    
    def identify_service(self, host: str, port: int) -> Optional[str]:
        """Attempt to identify a service by banner grabbing or probing."""
        if port in COMMON_SERVICES:
            return COMMON_SERVICES[port]
        
        # Try banner grabbing for common services
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((host, port))
            
            # Send appropriate probes
            if port == 80 or port == 8080:
                sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
            elif port == 22:
                # SSH: just receive banner
                pass
            elif port == 21:
                # FTP: just receive banner
                pass
            elif port == 25:
                # SMTP: just receive banner
                pass
            
            try:
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                sock.close()
                
                # Parse banner for service identification
                if 'SSH' in banner:
                    return 'SSH'
                if 'FTP' in banner:
                    return 'FTP'
                if '220' in banner:
                    return 'SMTP'
            except:
                pass
            
            sock.close()
        except:
            pass
        
        return 'unknown'