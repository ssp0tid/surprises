"""Port forwarding proxy module for PortPilot.

Provides simple TCP port forwarding proxy functionality.
"""

import socket
import threading
import select
import signal
import sys
from typing import Optional, Callable


class PortForwarder:
    """Simple TCP port forwarder."""
    
    def __init__(self, source_port: int, dest_host: str, dest_port: int,
                 buffer_size: int = 8192):
        """Initialize the port forwarder.
        
        Args:
            source_port: Local port to listen on.
            dest_host: Destination host to forward to.
            dest_port: Destination port.
            buffer_size: Buffer size for data transfer.
        """
        self.source_port = source_port
        self.dest_host = dest_host
        self.dest_port = dest_port
        self.buffer_size = buffer_size
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.client_sockets = []
        self.target_sockets = []
    
    def start(self) -> None:
        """Start the port forwarder."""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.source_port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            
            print(f"[*] Port forwarder started: 0.0.0.0:{self.source_port} -> {self.dest_host}:{self.dest_port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"[+] New connection from {addr[0]}:{addr[1]}")
                    self.client_sockets.append(client_socket)
                    
                    # Create target socket
                    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        target_socket.connect((self.dest_host, self.dest_port))
                        self.target_sockets.append(target_socket)
                        
                        # Start forwarding threads
                        client_thread = threading.Thread(
                            target=self._forward_data,
                            args=(client_socket, target_socket, "client->target"),
                            daemon=True
                        )
                        target_thread = threading.Thread(
                            target=self._forward_data,
                            args=(target_socket, client_socket, "target->client"),
                            daemon=True
                        )
                        
                        client_thread.start()
                        target_thread.start()
                        
                    except ConnectionRefusedError:
                        print(f"[-] Connection refused: {self.dest_host}:{self.dest_port}")
                        client_socket.close()
                        if target_socket in self.target_sockets:
                            self.target_sockets.remove(target_socket)
                        if client_socket in self.client_sockets:
                            self.client_sockets.remove(client_socket)
                        
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.running:
                        print(f"[-] Socket error: {e}")
                    break
                    
        except Exception as e:
            print(f"[-] Failed to start forwarder: {e}")
            raise
        finally:
            self.stop()
    
    def _forward_data(self, source: socket.socket, dest: socket.socket, direction: str) -> None:
        """Forward data between sockets.
        
        Args:
            source: Source socket.
            dest: Destination socket.
            direction: Direction string for logging.
        """
        try:
            while self.running:
                try:
                    data = source.recv(self.buffer_size)
                    if not data:
                        break
                    dest.sendall(data)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    break
        except Exception:
            pass
        finally:
            self._cleanup_pair(source, dest)
    
    def _cleanup_pair(self, client: socket.socket, target: socket.socket) -> None:
        """Clean up a pair of connected sockets."""
        try:
            client.close()
        except Exception:
            pass
        try:
            target.close()
        except Exception:
            pass
        
        if client in self.client_sockets:
            self.client_sockets.remove(client)
        if target in self.target_sockets:
            self.target_sockets.remove(target)
    
    def stop(self) -> None:
        """Stop the port forwarder."""
        self.running = False
        
        # Close all client sockets
        for sock in self.client_sockets:
            try:
                sock.close()
            except Exception:
                pass
        self.client_sockets.clear()
        
        # Close all target sockets
        for sock in self.target_sockets:
            try:
                sock.close()
            except Exception:
                pass
        self.target_sockets.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        
        print("[*] Port forwarder stopped")


class ForwarderManager:
    """Manager for multiple port forwarders."""
    
    def __init__(self):
        self.forwarders: dict[int, PortForwarder] = {}
        self.threads: dict[int, threading.Thread] = {}
    
    def start_forwarder(self, source_port: int, dest_host: str, dest_port: int) -> bool:
        """Start a new port forwarder.
        
        Args:
            source_port: Local port to listen on.
            dest_host: Destination host.
            dest_port: Destination port.
            
        Returns:
            True if started successfully, False otherwise.
        """
        if source_port in self.forwarders:
            print(f"[-] Forwarder already running on port {source_port}")
            return False
        
        forwarder = PortForwarder(source_port, dest_host, dest_port)
        thread = threading.Thread(target=forwarder.start, daemon=True)
        
        self.forwarders[source_port] = forwarder
        self.threads[source_port] = thread
        thread.start()
        
        # Give it a moment to start
        import time
        time.sleep(0.5)
        
        return forwarder.running
    
    def stop_forwarder(self, source_port: int) -> bool:
        """Stop a port forwarder.
        
        Args:
            source_port: Port of the forwarder to stop.
            
        Returns:
            True if stopped, False if not found.
        """
        if source_port not in self.forwarders:
            return False
        
        forwarder = self.forwarders[source_port]
        forwarder.stop()
        
        del self.forwarders[source_port]
        del self.threads[source_port]
        
        return True
    
    def stop_all(self) -> None:
        """Stop all forwarders."""
        for port in list(self.forwarders.keys()):
            self.stop_forwarder(port)
    
    def list_forwarders(self) -> list[dict]:
        """List all active forwarders.
        
        Returns:
            List of forwarder info dictionaries.
        """
        result = []
        for port, forwarder in self.forwarders.items():
            result.append({
                'source_port': port,
                'dest_host': forwarder.dest_host,
                'dest_port': forwarder.dest_port,
                'running': forwarder.running
            })
        return result


# Global forwarder manager instance
_manager: Optional[ForwarderManager] = None


def get_manager() -> ForwarderManager:
    """Get the global forwarder manager instance."""
    global _manager
    if _manager is None:
        _manager = ForwarderManager()
    return _manager


def setup_signal_handlers() -> None:
    """Set up signal handlers for clean shutdown."""
    def signal_handler(signum, frame):
        print("\n[*] Received signal, shutting down...")
        if _manager:
            _manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    # Simple test
    setup_signal_handlers()
    manager = get_manager()
    
    print("Starting test forwarder on port 8080 -> localhost:80")
    manager.start_forwarder(8080, 'localhost', 80)
    
    print("Press Ctrl+C to stop...")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_all()
