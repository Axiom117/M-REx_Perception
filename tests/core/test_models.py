"""Model layer tests: ``ToolHead`` factory and pose (M1)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import ToolHead, ToolState


def test_tool_head_for_workspace() -> None:
    tool = ToolHead.for_workspace(load_workspace("default"))
    assert tool.name == "adhesionTool"
    assert tool.contact_radius == pytest.approx(0.25)
    assert tool.diameter == pytest.approx(1.5)
    assert tool.radius == pytest.approx(0.75)
    assert tool.height == pytest.approx(0.5)
    assert tool.clearance == pytest.approx(1.0)
    assert tool.shape == "cylinder"
    assert tool.adhesion_model == "vanDerWaalsDroplet"
    # source region is [0, 5, ...] -> [0/2 + 15, 5/2 + 15, 10]
    assert tool.position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.home_position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.target_position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.state == ToolState.HOME
    assert not tool.has_embryo
    assert tool.attached_embryo_id == 0
    # pose is derived from position/orientation
    tool.position = np.array([1.0, 2.0, 3.0])
    tool.orientation = rotation_z(0.25)
    assert tool.pose[:3, :3] == pytest.approx(rotation_z(0.25))
    assert tool.pose[:3, 3] == pytest.approx([1.0, 2.0, 3.0])
    assert tool.pose[3] == pytest.approx([0.0, 0.0, 0.0, 1.0])
