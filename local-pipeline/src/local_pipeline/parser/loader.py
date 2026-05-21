"""YAML loader for pipeline definitions."""

import os
import re
from pathlib import Path

import yaml

from .models import PipelineDefinition, interpolate_env_vars


def load_yaml_file(path: Path | str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Pipeline file not found: {path}")

    content = path.read_text()
    content = interpolate_env_vars(content)
    data = yaml.safe_load(content)
    return data


def parse_pipeline(content: str) -> PipelineDefinition:
    content = interpolate_env_vars(content)
    data = yaml.safe_load(content)
    return PipelineDefinition(**data)


def load_pipeline(path: Path | str) -> PipelineDefinition:
    path = Path(path)
    content = path.read_text()
    return parse_pipeline(content)
