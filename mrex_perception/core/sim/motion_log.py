"""Tool motion logging (ports of ``initializeMotionLog.m`` / ``recordToolMotion.m``).

``MotionLog`` mirrors the MATLAB struct field-for-field:

===============  ========  ===============================================
field            shape     content
===============  ========  ===============================================
``positions``    (N, 3)    tool translation in mm
``rotation``     (N, 3)    ZYX euler angles (roll, pitch, yaw), radians
``tool_state``   (N,)      tool state string per sample
``move_yaw_changes`` (M,)  |shortest yaw delta| per ``move_tool`` call
===============  ========  ===============================================

The ZYX extraction follows ``recordToolMotion.m`` line-by-line, including the
gimbal-lock fallback (``|cos(pitch)| <= 1e-8``). Samples are stored in plain
lists internally (O(1) appends) and exposed as fresh numpy arrays.
"""

from __future__ import annotations

from typing import Any, Protocol

import numpy as np


class LoggableTool(Protocol):
    """Anything exposing a 4x4 ``pose`` (``ToolHead`` or a lightweight test stub)."""

    @property
    def pose(self) -> np.ndarray: ...


def extract_zyx_angles(rotation: np.ndarray) -> np.ndarray:
    """Extract ``(roll, pitch, yaw)`` from a 3x3 rotation matrix.

    Port of the extraction step in ``recordToolMotion.m``; falls back to
    ``roll = 0`` when ``|cos(pitch)| <= 1e-8`` (gimbal lock).
    """
    r = np.asarray(rotation, dtype=float)
    pitch = float(np.arctan2(-r[2, 0], np.hypot(r[0, 0], r[1, 0])))
    if abs(np.cos(pitch)) > 1e-8:
        roll = float(np.arctan2(r[2, 1], r[2, 2]))
        yaw = float(np.arctan2(r[1, 0], r[0, 0]))
    else:
        roll = 0.0
        yaw = float(np.arctan2(-r[0, 1], r[1, 1]))
    return np.array([roll, pitch, yaw])


class MotionLog:
    """Append-only motion history (field table in the module docstring)."""

    def __init__(self) -> None:
        self._positions: list[np.ndarray] = []
        self._rotation: list[np.ndarray] = []
        self._tool_state: list[str] = []
        self._move_yaw_changes: list[float] = []

    def __len__(self) -> int:
        return len(self._positions)

    def record(self, tool: LoggableTool) -> None:
        """Append one sample (port of ``recordToolMotion.m``).

        Position and rotation are read from ``tool.pose`` exactly like MATLAB;
        a missing ``state`` attribute is recorded as ``"unknown"``.
        """
        pose = np.asarray(tool.pose, dtype=float)
        self._positions.append(pose[:3, 3].copy())
        self._rotation.append(extract_zyx_angles(pose[:3, :3]))
        state = getattr(tool, "state", "unknown")
        self._tool_state.append(str(state))

    def record_move_yaw_change(self, magnitude: float) -> None:
        """Append one |shortest yaw delta| (radians), as ``moveTool.m`` does."""
        self._move_yaw_changes.append(float(magnitude))

    # -- read-only views (fresh arrays; safe to hand to numpy code) ----------

    @property
    def positions(self) -> np.ndarray:
        """(N, 3) tool positions in mm."""
        return np.asarray(self._positions, dtype=float).reshape(-1, 3)

    @property
    def rotation(self) -> np.ndarray:
        """(N, 3) ZYX euler angles (roll, pitch, yaw) in radians."""
        return np.asarray(self._rotation, dtype=float).reshape(-1, 3)

    @property
    def tool_state(self) -> np.ndarray:
        """(N,) tool state label per sample."""
        return np.asarray(self._tool_state, dtype=str)

    @property
    def move_yaw_changes(self) -> np.ndarray:
        """(M,) |shortest yaw delta| per ``move_tool`` call, radians."""
        return np.asarray(self._move_yaw_changes, dtype=float)

    def to_dict(self) -> dict[str, Any]:
        """Plain-python snapshot (JSON ready) for reports / exports."""
        return {
            "positions": self.positions.tolist(),
            "rotation": self.rotation.tolist(),
            "tool_state": list(self._tool_state),
            "move_yaw_changes": list(self._move_yaw_changes),
        }
