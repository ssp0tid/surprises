"""Schema validation for pipeline YAML."""

import json
from pathlib import Path

from .models import PipelineDefinition, validate_circular_dependencies


PIPELINE_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["name", "tasks"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "version": {"type": "string", "default": "1.0"},
        "triggers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string", "enum": ["cron", "manual", "webhook", "interval"]},
                    "cron": {"type": "string"},
                    "seconds": {"type": "integer"},
                },
            },
        },
        "retry": {
            "type": "object",
            "properties": {
                "max_attempts": {"type": "integer", "minimum": 1},
                "backoff_factor": {"type": "number", "minimum": 1},
                "initial_delay": {"type": "number", "minimum": 0},
            },
        },
        "default_timeout": {"type": "integer", "minimum": 1},
        "tasks": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "name", "type"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["shell", "python", "http"]},
                    "command": {"type": "string"},
                    "script": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}},
                    "method": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "headers": {"type": "object"},
                    "body": {"type": "object"},
                    "env": {"type": "object"},
                    "output_file": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "timeout": {"type": "integer"},
                    "retry": {"type": "object"},
                },
            },
        },
    },
}


def validate_pipeline(data: dict) -> PipelineDefinition:
    pipeline = PipelineDefinition(**data)
    if validate_circular_dependencies(pipeline.tasks):
        raise ValueError("Circular dependency detected in pipeline tasks")
    return pipeline


def validate_yaml_file(path: Path) -> list[str]:
    from .loader import load_yaml_file

    errors = []
    try:
        data = load_yaml_file(path)
        validate_pipeline(data)
    except Exception as e:
        errors.append(str(e))
    return errors
