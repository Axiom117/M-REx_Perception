"""Tool head creation (port of ``src/setup/createToolHead.m``)."""

from __future__ import annotations

import numpy as np

from mrex_perception.core.models import ToolHead, Workspace


def create_tool_head(workspace: Workspace) -> ToolHead:
    """Create the adhesion tool head with its initial (home) position.

    The initial position is derived from the source region:
    ``[source_x / 2 + 15, source_y / 2 + 15, 10]`` -> ``[15, 17.5, 10]`` for
    the default config. Home and target position start at the same point.
    """
    position = np.array(
        [
            workspace.source_region[0] / 2 + 15,
            workspace.source_region[1] / 2 + 15,
            10.0,
        ]
    )
    tool = ToolHead(position=position)
    tool.home_position = position.copy()
    tool.target_position = position.copy()
    return tool
