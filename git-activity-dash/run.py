#!/usr/bin/env python3
"""Development entry point for Git Activity Dashboard."""

import os
import yaml
from app import create_app


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


if __name__ == "__main__":
    config = load_config()
    app_config = config.get("app", {})

    app = create_app()

    host = app_config.get("host", "0.0.0.0")
    port = app_config.get("port", 5000)
    debug = app_config.get("debug", True)

    print(f"Starting Git Activity Dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
