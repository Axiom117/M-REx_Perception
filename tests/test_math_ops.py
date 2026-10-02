"""Math helpers: rotation_z and make_pose. M1."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.core.math_ops import make_pose, rotation_z


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
