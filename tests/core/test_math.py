"""Math layer tests: transforms (rotation_z / make_pose) + geometry (M1)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import make_pose, pixel_to_workspace, rotation_z


@pytest.fixture()
def workspace():
    return load_workspace("default")


# Hand-computed samples; the same values are cross-checked against MATLAB
# output during M1 verification (see doc/migration-plan.md).
def test_center_pixel(workspace) -> None:
    pos = pixel_to_workspace(500, 250, 1000, 500, workspace)
    assert pos == pytest.approx([10.0, 17.5, 0.1])


def test_image_y_axis_is_flipped(workspace) -> None:
    # top-left pixel (0, 0) maps to the far y edge of the source region
    assert pixel_to_workspace(0, 0, 1000, 500, workspace) == pytest.approx([0.0, 30.0, 0.1])
    assert pixel_to_workspace(1000, 500, 1000, 500, workspace) == pytest.approx([20.0, 5.0, 0.1])


def test_midpoint(workspace) -> None:
    assert pixel_to_workspace(250, 125, 1000, 500, workspace) == pytest.approx([5.0, 23.75, 0.1])


def test_non_square_image(workspace) -> None:
    pos = pixel_to_workspace(640, 480, 1280, 720, workspace)
    assert pos == pytest.approx([10.0, 5 + 25 * (240 / 720), 0.1])


# -- transforms (rotation_z / make_pose) ---------------------------------------


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
