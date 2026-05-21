"""Flask application for DevDash."""

import os
import yaml
from flask import Flask, render_template, jsonify, abort
from .models.service import Service
from .services.discoverer import ServiceDiscoverer


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'config.yaml'
    )
    if os.path.exists(config_path):
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    app.config['DEVDASH_CONFIG'] = config
    
    # Initialize discoverer
    discovery_config = config.get('discovery', {})
    ports = discovery_config.get('ports', list(range(3000, 9001)))
    app.config['DISCOVERER'] = ServiceDiscoverer(scan_ports=ports)
    
    @app.route('/')
    def index():
        """Render the dashboard."""
        return render_template('index.html')
    
    @app.route('/api/services')
    def list_services():
        """List all discovered services."""
        discoverer = app.config['DISCOVERER']
        services = discoverer.discover()
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in services],
            'count': len(services)
        })
    
    @app.route('/api/services/<service_id>')
    def get_service(service_id):
        """Get details for a specific service."""
        discoverer = app.config['DISCOVERER']
        services = discoverer.discover()
        
        for service in services:
            if service.id == service_id:
                return jsonify({
                    'success': True,
                    'data': service.to_dict()
                })
        
        abort(404, description="Service not found")
    
    @app.route('/api/ports')
    def list_ports():
        """List all ports in use by dev servers."""
        discoverer = app.config['DISCOVERER']
        services = discoverer.discover()
        ports = [s.port for s in services]
        
        return jsonify({
            'success': True,
            'data': ports,
            'count': len(ports)
        })
    
    @app.route('/api/system')
    def system_stats():
        """Get system-wide stats."""
        discoverer = app.config['DISCOVERER']
        services = discoverer.discover()
        
        total_cpu = sum(s.cpu_percent for s in services)
        total_memory = sum(s.memory_mb for s in services)
        
        import psutil
        return jsonify({
            'success': True,
            'data': {
                'service_count': len(services),
                'total_cpu_percent': round(total_cpu, 1),
                'total_memory_mb': round(total_memory, 1),
                'cpu_count': psutil.cpu_count(),
                'memory_total_mb': round(psutil.virtual_memory().total / 1024 / 1024, 1)
            }
        })
    
    return app