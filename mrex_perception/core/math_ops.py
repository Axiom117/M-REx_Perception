"""Mathematical operations shared across the core layer.

Pure math only: no domain types (Workspace / Embryo / ...) are imported here,
so every module can depend on it. Domain-specific coordinate mapping
(pixel -> workspace) stays in ``mrex_perception.core.geometry``.
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
