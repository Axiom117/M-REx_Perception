"""Model layer tests: ``ToolHead`` factory and pose (M1)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import EmbryoSpec, ToolHead, ToolState


def test_tool_head_for_workspace() -> None:
    tool = ToolHead.for_workspace(load_workspace("default"))
    assert tool.name == "adhesionTool"
    assert tool.contact_radius == pytest.approx(0.25)
    assert tool.contact_shape == "circular"
    assert tool.diameter == pytest.approx(1.5)
    assert tool.radius == pytest.approx(0.75)
    assert tool.height == pytest.approx(0.5)
    assert tool.clearance == pytest.approx(1.0)
    assert tool.shape == "cylinder"
    assert tool.adhesion_model == "vanDerWaalsDroplet"
    assert tool.base_probability == pytest.approx(0.7)
    assert tool.reference_width == pytest.approx(0.2)
    assert tool.attempt_penalty == pytest.approx(0.05)
    assert tool.max_attempts == 3
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


def test_tool_head_home_offset_override() -> None:
    tool = ToolHead.for_workspace(load_workspace("default"), home_offset=(0.0, 0.0, 0.0))
    assert tool.position == pytest.approx([0.0, 2.5, 0.0])
    assert tool.home_position == pytest.approx([0.0, 2.5, 0.0])
    assert tool.target_position == pytest.approx([0.0, 2.5, 0.0])


def test_embryo_spec_defaults() -> None:
    spec = EmbryoSpec()
    assert (spec.shape, spec.width, spec.length, spec.height) == ("ellipsoid", 0.2, 0.5, 0.2)
    assert spec.min_confidence == pytest.approx(0.8)
    assert spec.cluster_threshold == pytest.approx(1.0)
    assert spec.min_spacing == pytest.approx(1.0)
