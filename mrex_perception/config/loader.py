"""Shared mechanics for loading YAML config files.

Single place in the app that touches config files on disk: resolving
``<name>.yaml`` inside a config directory, reading and parsing the YAML,
and producing clear errors. Per-type modules (``workspace``, ``embryo``,
``tool_head``, and future ``app_settings``) define their own schema models on
top of these helpers, so new config types plug in without duplicating file
handling.

This module belongs to the config boundary layer: it may touch the file
system, but never the other way around (``core`` stays I/O-free).
"""

# Make type hints work with forward references
from __future__ import annotations

# Iterable represents any object that can be iterated over (list, tuple, etc.)
from collections.abc import Iterable

# Path represents filesystem paths, usages: Path("some/file.txt"), Path("/absolute/path")
from pathlib import Path

# PyYAML is used for parsing YAML files as Python dict
import yaml


# Find the absolute path to the repository-level config directory
def config_root() -> Path:
    """Repository-level ``config/`` directory.

    The directory ships as an external resource in packaged builds; 
    a future milestone can make this configurable.
    """
    return Path(__file__).resolve().parents[2] / "config"

# Load a YAML config file as a mapping (dict)
def load_config_mapping(config_name: str, directory: Path, label: str) -> dict:
    """Resolve and read a YAML config file, requiring a top-level mapping."""

    # Only ".yaml" is supported (project convention): the candidate path is unique
    config_path = directory / f"{config_name}.yaml"

    # The config file must exist on disk
    if not config_path.is_file():
        raise FileNotFoundError(f"{label} file not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{label} is not a mapping: {config_path}")
    return data

# Require that certain fields exist in a config mapping
def require_fields(data: dict, required_fields: Iterable[str], label: str) -> None:
    """Raise if any required key is missing from ``data`` (MATLAB-like wording)."""
    missing = [key for key in required_fields if key not in data]
    if missing:
        raise ValueError(f"{label} is missing fields: " + ", ".join(missing))
