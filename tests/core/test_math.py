"""Math layer tests: transforms (rotation_z / make_pose) + geometry (M1)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import make_pose, pixel_to_workspace, rotation_z


def test_rotation_z_conventions() -> None:
    assert rotation_z(0.0) == pytest.approx(np.eye(3))
    quarter_turn = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    assert rotation_z(np.pi / 2) == pytest.approx(quarter_turn)
    assert np.linalg.det(rotation_z(1.234)) == pytest.approx(1.0)


def test_make_pose_assembles_rotation_and_translation() -> None:
    pose = make_pose(rotation_z(0.5), np.array([1.0, 2.0, 3.0]))
    assert pose.shape == (4, 4)
    assert pose[:3, :3] == pytest.approx(rotation_z(0.5))
    assert pose[:3, 3] == pytest.approx([1.0, 2.0, 3.0])
    assert pose[3] == pytest.approx([0.0, 0.0, 0.0, 1.0])


def test_pixel_to_workspace_samples() -> None:
    """Hand-computed samples; image y is flipped relative to the workspace axis."""
    ws = load_workspace("default")
    assert pixel_to_workspace(500, 250, 1000, 500, ws) == pytest.approx([10.0, 17.5, 0.1])
    assert pixel_to_workspace(0, 0, 1000, 500, ws) == pytest.approx([0.0, 30.0, 0.1])
    assert pixel_to_workspace(1000, 500, 1000, 500, ws) == pytest.approx([20.0, 5.0, 0.1])
    assert pixel_to_workspace(250, 125, 1000, 500, ws) == pytest.approx([5.0, 23.75, 0.1])
    assert pixel_to_workspace(640, 480, 1280, 720, ws) == pytest.approx(
        [10.0, 5 + 25 * (240 / 720), 0.1]
    )
