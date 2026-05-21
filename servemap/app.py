#!/usr/bin/env python3
"""
ServiceMap - Local Network Service Discovery and Visualization
Flask web application for discovering and visualizing network services.
"""

from flask import Flask, render_template, jsonify, request
import asyncio
import threading
from scanner import ServiceScanner, PortScanner

app = Flask(__name__)

# Global scanner instance
service_scanner = ServiceScanner()
port_scanner = PortScanner()

# Store discovered services
discovered_services = []


def run_async_scan(services_list, timeout=5):
    """Run async service discovery in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(
            service_scanner.discover_all_services(timeout=timeout)
        )
        services_list.extend(results)
    finally:
        loop.close()


@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')


@app.route('/api/scan', methods=['POST'])
def scan_network():
    """Start a network scan."""
    global discovered_services
    
    data = request.get_json() or {}
    timeout = data.get('timeout', 5)
    port_range = data.get('port_range', [1, 1024])
    
    discovered_services = []
    
    # Run mDNS/DNS-SD discovery in background thread
    mdns_thread = threading.Thread(target=run_async_scan, 
                                    args=(discovered_services, timeout))
    mdns_thread.start()
    mdns_thread.join()
    
    # Run port scanning on common local network subnets
    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    subnet = '.'.join(local_ip.split('.')[:3])
    
    # Scan common IPs in the subnet
    for host_idx in range(1, 255, 10):  # Sample IPs to avoid long scans
        host = f"{subnet}.{host_idx}"
        ports = port_scanner.scan_host(host, port_range[0], port_range[1])
        if ports:
            for port, service in ports:
                discovered_services.append({
                    'name': service,
                    'type': 'discovered',
                    'host': host,
                    'port': port,
                    'protocol': 'tcp'
                })
    
    return jsonify({
        'status': 'success',
        'services': discovered_services,
        'count': len(discovered_services)
    })


@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all discovered services."""
    return jsonify({
        'services': discovered_services,
        'count': len(discovered_services)
    })


@app.route('/api/scan/port', methods=['POST'])
def scan_port():
    """Scan a specific host for open ports."""
    data = request.get_json() or {}
    host = data.get('host', 'localhost')
    start_port = data.get('start_port', 1)
    end_port = data.get('end_port', 1024)
    
    results = port_scanner.scan_host(host, start_port, end_port)
    
    return jsonify({
        'host': host,
        'ports': results,
        'count': len(results)
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)