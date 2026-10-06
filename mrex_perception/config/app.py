"""Aggregate app config handed to the entry layers (GUI / CLI).

Approach A: the aggregate carries already-validated core objects (today only
``Workspace``), so consumers receive ready-to-use data and never touch the
file system themselves. Future sections (tool head, app defaults from
``config/app.yaml``) plug in as new fields here, so consumer constructor
signatures stay unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.models import Workspace


@dataclass(frozen=True, eq=False)
class AppConfig:
    """One app session's validated configuration (core-side objects)."""

    workspace: Workspace


def load_app_config(workspace_name: str = "default", config_dir: Path | None = None) -> AppConfig:
    """Load the aggregate config (Phase 1: the workspace section only)."""
    return AppConfig(workspace=load_workspace(workspace_name, config_dir=config_dir))
