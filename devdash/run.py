#!/usr/bin/env python3
"""DevDash - Entry Point"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from devdash.app import create_app

def main():
    app = create_app()
    config = app.config.get('DEVDASH_CONFIG', {})
    host = config.get('devdash', {}).get('host', '127.0.0.1')
    port = config.get('devdash', {}).get('port', 7890)
    debug = config.get('devdash', {}).get('debug', False)
    
    print(f"Starting DevDash on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()