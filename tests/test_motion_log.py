"""MotionLog recording + ZYX extraction (M2)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import make_pose, rotation_z
from mrex_perception.core.models import ToolState
from mrex_perception.core.setup import create_tool_head
from mrex_perception.core.sim import MotionLog, extract_zyx_angles, record_tool_motion


class _StubTool:
    """Duck-typed tool exposing only ``pose`` / optional ``state``."""

    def __init__(self, pose: np.ndarray, state: object = None) -> None:
        self.pose = pose
        if state is not None:
            self.state = state


# Ry(+-pi/2) literals for the gimbal-lock cases.
_RY_POS = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
_RY_NEG = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])


def test_empty_log() -> None:
    log = MotionLog()
    assert len(log) == 0
    assert log.positions.shape == (0, 3)
    assert log.rotation.shape == (0, 3)
    assert log.tool_state.tolist() == []
    assert log.move_yaw_changes.shape == (0,)


def test_record_reads_pose_and_state() -> None:
    log = MotionLog()
    pose = make_pose(rotation_z(0.4), np.array([1.0, 2.0, 3.0]))
    log.record(_StubTool(pose, state="grasped"))
    assert len(log) == 1
    assert log.positions.tolist() == [[1.0, 2.0, 3.0]]
    np.testing.assert_allclose(log.rotation, [[0.0, 0.0, 0.4]], rtol=0, atol=1e-12)
    assert log.tool_state.tolist() == ["grasped"]


def test_record_missing_state_is_unknown() -> None:
    log = MotionLog()
    log.record(_StubTool(np.eye(4)))
    assert log.tool_state.tolist() == ["unknown"]


def test_record_tool_head_uses_enum_value() -> None:
    tool = create_tool_head(load_workspace("default"))
    log = record_tool_motion(MotionLog(), tool)
    assert log.tool_state.tolist() == [ToolState.HOME.value]


def test_extract_zyx_pure_yaw() -> None:
    angles = extract_zyx_angles(rotation_z(0.3))
    assert angles == pytest.approx([0.0, 0.0, 0.3], abs=1e-12)


def test_gimbal_lock_positive_pitch_uses_fallback() -> None:
    rotation = rotation_z(0.7) @ _RY_POS
    angles = extract_zyx_angles(rotation)
    assert angles == pytest.approx([0.0, np.pi / 2, 0.7], abs=1e-12)


def test_gimbal_lock_negative_pitch_uses_fallback() -> None:
    rotation = rotation_z(0.7) @ _RY_NEG
    angles = extract_zyx_angles(rotation)
    assert angles == pytest.approx([0.0, -np.pi / 2, 0.7], abs=1e-12)


def test_move_yaw_changes_recording() -> None:
    log = MotionLog()
    log.record_move_yaw_change(0.25)
    log.record_move_yaw_change(0.5)
    assert log.move_yaw_changes.tolist() == [0.25, 0.5]


def test_to_dict_is_plain_python() -> None:
    log = MotionLog()
    log.record(_StubTool(make_pose(np.eye(3), np.array([1.0, 0.0, 0.0]))))
    log.record_move_yaw_change(0.1)
    data = log.to_dict()
    assert data["positions"] == [[1.0, 0.0, 0.0]]
    assert data["rotation"] == [[0.0, 0.0, 0.0]]
    assert data["tool_state"] == ["unknown"]
    assert data["move_yaw_changes"] == [0.1]
