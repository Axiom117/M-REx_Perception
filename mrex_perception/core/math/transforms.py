"""Rigid transforms shared across the core layer (rotation_z / make_pose).

Pure math only: no domain types (Workspace / Embryo / ...) are imported here.
The pixel -> workspace mapping stays in ``mrex_perception.core.math.geometry``.
"""

from __future__ import annotations

import numpy as np


def rotation_z(yaw: float) -> np.ndarray:
    """3x3 rotation matrix about the z axis (same construction as MATLAB Rz)."""
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def make_pose(orientation: np.ndarray, position: np.ndarray) -> np.ndarray:
    """Assemble a 4x4 homogeneous transform (pose) from rotation + position."""
    pose = np.eye(4)
    pose[:3, :3] = orientation
    pose[:3, 3] = position
    return pose
