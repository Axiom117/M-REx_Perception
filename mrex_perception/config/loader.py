"""Shared mechanics for loading YAML config files.

Single place in the app that touches config files on disk: resolving
``<name>.yaml`` / ``<name>.yml`` inside a config directory, reading and
parsing the YAML, and producing clear errors. Per-type modules (``workspace``,
and future ``embryo`` / ``app_settings``) define their own schema models on
top of these helpers, so new config types plug in without duplicating file
handling.

This module belongs to the config boundary layer: it may touch the file
system, but never the other way around (``core`` stays I/O-free).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import yaml


# Find the absolute path to the repository-level config directory
def config_root() -> Path:
    """Repository-level ``config/`` directory.

    The directory ships as an external resource in packaged builds (see the
    migration plan M7); a future milestone can make this configurable.
    """
    return Path(__file__).resolve().parents[2] / "config"

# Load a YAML config file as a mapping (dict)
def load_config_mapping(config_name: str, directory: Path, label: str) -> dict:
    """Resolve and read a YAML config file, requiring a top-level mapping."""

    # Assemble the list of candidate file paths with .yaml and .yml extensions
    candidates = [directory / f"{config_name}{suffix}" for suffix in (".yaml", ".yml")]

    # Find the first candidate that exists on disk
    config_path = next((path for path in candidates if path.is_file()), None)
    if config_path is None:
        raise FileNotFoundError(f"{label} file not found: {candidates[0]}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{label} is not a mapping: {config_path}")
    return data


def require_fields(data: dict, required_fields: Iterable[str], label: str) -> None:
    """Raise if any required key is missing from ``data`` (MATLAB-like wording)."""
    missing = [key for key in required_fields if key not in data]
    if missing:
        raise ValueError(f"{label} is missing fields: " + ", ".join(missing))
