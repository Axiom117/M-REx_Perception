"""Aggregate app config handed to the entry layers (GUI / CLI).

The aggregate carries validated values that consumers use directly and never
re-reads files itself. ``workspace`` / ``embryo`` are ready-to-use core data
objects; ``tool`` stays a ``ToolHeadConfig`` factory because a tool head is
stateful -- every run materialises a fresh instance via
``ToolHeadConfig.to_tool_head(workspace)``. Future sections (app defaults
from ``config/app.yaml``) plug in as new fields here, so consumer constructor
signatures stay unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mrex_perception.config.embryo import load_embryo
from mrex_perception.config.tool_head import ToolHeadConfig, load_tool_head
from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.models import EmbryoSpec, Workspace


@dataclass(frozen=True, eq=False)
class AppConfig:
    """One app session's validated configuration (core data + tool factory)."""

    workspace: Workspace
    embryo: EmbryoSpec
    tool: ToolHeadConfig


def load_app_config(
    workspace_name: str = "default",
    tool_name: str = "default",
    embryo_name: str = "default",
    config_dir: Path | None = None,
) -> AppConfig:
    """Load the aggregate config (workspace + embryo + tool head sections).

    ``config_dir`` overrides the repository ``config/`` root (the directory
    holding ``workspace/``, ``embryo/`` and ``tool_head/``); ``None`` uses the
    shipped configs.
    """
    root = Path(config_dir) if config_dir is not None else None
    return AppConfig(
        workspace=load_workspace(
            workspace_name, config_dir=None if root is None else root / "workspace"
        ),
        embryo=load_embryo(embryo_name, config_dir=None if root is None else root / "embryo"),
        tool=load_tool_head(tool_name, config_dir=None if root is None else root / "tool_head"),
    )
