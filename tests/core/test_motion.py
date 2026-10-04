"""Motion layer tests: move_tool wrappers + MotionLog / ZYX extraction (M2)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import Embryo, EmbryoState, ToolHead, ToolState
from mrex_perception.core.sim import (
    MotionLog,
    extract_zyx_angles,
    move_tool,
    move_tool_final,
    move_tool_to_embryo,
    raise_tool,
    return_home,
)

START = np.array([15.0, 17.5, 10.0])


class _StopAfter:
    """Stop token that reports ``False`` for the first ``allowed`` checks."""

    def __init__(self, allowed: int) -> None:
        self.allowed = allowed
        self.calls = 0

    def is_set(self) -> bool:
        self.calls += 1
        return self.calls > self.allowed


# Ry(+-pi/2) literals for the gimbal-lock cases.
_RY_POS = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
_RY_NEG = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])


def _tool() -> ToolHead:
    tool = ToolHead(position=START.copy())
    tool.home_position = START.copy()
    return tool


# -- move_tool ---------------------------------------------------------------


def test_move_tool_records_full_trajectory() -> None:
    tool = _tool()
    log = MotionLog()
    target = np.array([25.0, 17.5, 10.0])

    move_tool([], tool, target, 0.0, 50, log)

    assert len(log) == 50
    assert log.tool_state.tolist() == ["home"] * 50
    expected = np.array([(1 - k / 50) * START + (k / 50) * target for k in range(1, 51)])
    np.testing.assert_allclose(log.positions, expected, rtol=0, atol=1e-12)
    np.testing.assert_allclose(log.rotation, np.zeros((50, 3)), rtol=0, atol=1e-12)
    assert log.move_yaw_changes == pytest.approx([0.0])
    assert tool.position == pytest.approx(target)
    assert tool.target_position == pytest.approx(target)


def test_move_tool_shortest_angle_crosses_pi() -> None:
    tool = _tool()
    tool.orientation = rotation_z(np.deg2rad(170.0))
    log = MotionLog()

    move_tool([], tool, tool.position, np.deg2rad(-170.0), 20, log)

    assert log.move_yaw_changes == pytest.approx([np.deg2rad(20.0)], abs=1e-12)
    yaws = log.rotation[:, 2]
    assert yaws[9] == pytest.approx(np.pi, abs=1e-12)  # halfway -> through 180
    assert yaws[-1] == pytest.approx(np.deg2rad(-170.0), abs=1e-12)
    # monotonic from 170 to (unwrapped) 190 degrees, not the 340 degree way
    assert np.all(np.diff(np.unwrap(yaws)) > 0)


def test_move_tool_rejects_bad_target_rotation() -> None:
    with pytest.raises(ValueError, match="3-by-3"):
        move_tool([], _tool(), START, np.zeros((2, 2)), 5, MotionLog())


def test_move_tool_stop_token_breaks_midway() -> None:
    tool = _tool()
    log = MotionLog()
    target = np.array([25.0, 17.5, 10.0])
    token = _StopAfter(10)

    move_tool([], tool, target, 0.0, 50, log, stop_token=token)

    assert len(log) == 10
    alpha = 10 / 50
    assert tool.position == pytest.approx((1 - alpha) * START + alpha * target)
    # target_position is still set after a stopped move (MATLAB order)
    assert tool.target_position == pytest.approx(target)


def test_move_tool_attached_embryo_follows_every_step() -> None:
    embryo = Embryo(id=1, position=np.array([5.0, 5.0, 0.1]))
    tool = _tool()
    tool.position = np.array([5.0, 5.0, 2.0])
    tool.has_embryo = True
    tool.attached_embryo_id = 1
    log = MotionLog()
    target = np.array([7.0, 8.0, 2.0])

    sampled: list[tuple[np.ndarray, np.ndarray]] = []

    def on_step() -> None:
        sampled.append((tool.position.copy(), embryo.position.copy()))

    move_tool([embryo], tool, target, rotation_z(0.4), 40, log, on_step=on_step)

    assert len(sampled) == 40  # on_step fires once per interpolation step
    for tool_position, embryo_position in sampled:
        assert embryo_position == pytest.approx(tool_position - np.array([0.0, 0.0, 1.0]))
    assert tool.position == pytest.approx(target)
    assert embryo.position == pytest.approx([7.0, 8.0, 1.0])
    assert embryo.orientation == pytest.approx(rotation_z(0.4), abs=1e-12)

    # copies, not aliases (MATLAB value semantics)
    tool.orientation[0, 0] = 999.0
    assert embryo.orientation[0, 0] != 999.0


# -- wrappers ----------------------------------------------------------------


def test_move_tool_to_embryo() -> None:
    embryo = Embryo(
        id=1,
        position=np.array([5.0, 8.0, 0.1]),
        orientation=rotation_z(0.5),
        state=EmbryoState.SELECTED,
    )
    tool = _tool()
    log = MotionLog()

    move_tool_to_embryo([embryo], tool, 10, log)

    assert len(log) == 10
    assert tool.state == ToolState.ABOVE_EMBRYO
    assert tool.position == pytest.approx(embryo.position + np.array([0.0, 0.0, 1.0]))
    assert tool.orientation == pytest.approx(rotation_z(0.5), abs=1e-9)


def test_move_tool_final() -> None:
    embryo = Embryo(id=1, position=np.array([5.0, 5.0, 0.1]))
    tool = _tool()
    tool.has_embryo = True
    tool.attached_embryo_id = 1
    moved = np.array([81.0, 6.0, 0.1])
    log = MotionLog()

    move_tool_final([embryo], tool, 10, log, moved)

    assert len(log) == 10
    assert tool.state == ToolState.ABOVE_MOVED_POSITION
    assert tool.position == pytest.approx(moved + np.array([0.0, 0.0, 1.0]))
    # follows: tool - clearance = moved_position
    assert embryo.position == pytest.approx(moved)


def test_raise_and_return_home() -> None:
    tool = _tool()
    tool.position = np.array([5.0, 6.0, 2.0])
    tool.orientation = rotation_z(0.7)
    log = MotionLog()

    raise_tool([], tool, 10, log)
    assert tool.position == pytest.approx([5.0, 6.0, 3.0])
    assert tool.state == ToolState.LIFTED

    return_home([], tool, 10, log)
    assert len(log) == 20
    assert tool.position == pytest.approx(START)
    assert tool.orientation == pytest.approx(np.eye(3), abs=1e-9)
    assert tool.state == ToolState.HOME
    assert log.move_yaw_changes[-1] == pytest.approx(0.7, abs=1e-12)


def test_wrappers_warn_when_target_missing() -> None:
    tool = _tool()
    log = MotionLog()

    with pytest.warns(UserWarning, match="No selected embryo found"):
        move_tool_to_embryo([Embryo(id=1)], tool, 10, log)
    assert len(log) == 0
    assert tool.state == ToolState.HOME

    with pytest.warns(UserWarning, match="Tool has no attached embryo"):
        move_tool_final([], tool, 10, log, np.zeros(3))


# -- MotionLog recording / ZYX extraction -------------------------------------


def test_motion_log_recording() -> None:
    log = MotionLog()
    assert len(log) == 0
    assert log.positions.shape == (0, 3)
    assert log.rotation.shape == (0, 3)
    assert log.tool_state.tolist() == []

    grasped = ToolHead(
        position=np.array([1.0, 2.0, 3.0]),
        orientation=rotation_z(0.4),
        state=ToolState.GRASPED,
    )
    log.record(grasped)
    assert len(log) == 1
    assert log.positions.tolist() == [[1.0, 2.0, 3.0]]
    np.testing.assert_allclose(log.rotation, [[0.0, 0.0, 0.4]], rtol=0, atol=1e-12)
    assert log.tool_state.tolist() == ["grasped"]

    log.record(ToolHead())  # default pose (origin, identity) and state -> "home"
    log.record(ToolHead.for_workspace(load_workspace("default")))
    assert log.tool_state.tolist() == ["grasped", "home", "home"]


def test_extract_zyx_angles() -> None:
    assert extract_zyx_angles(rotation_z(0.3)) == pytest.approx([0.0, 0.0, 0.3], abs=1e-12)
    # gimbal lock (|cos(pitch)| <= 1e-8) takes the roll=0 fallback branch
    locked_pos = rotation_z(0.7) @ _RY_POS
    assert extract_zyx_angles(locked_pos) == pytest.approx([0.0, np.pi / 2, 0.7], abs=1e-12)
    locked_neg = rotation_z(0.7) @ _RY_NEG
    assert extract_zyx_angles(locked_neg) == pytest.approx([0.0, -np.pi / 2, 0.7], abs=1e-12)


def test_move_yaw_changes_and_to_dict() -> None:
    log = MotionLog()
    log.record(ToolHead(position=np.array([1.0, 0.0, 0.0])))
    log.record_move_yaw_change(0.25)
    log.record_move_yaw_change(0.5)
    assert log.move_yaw_changes.tolist() == [0.25, 0.5]

    data = log.to_dict()
    assert data["positions"] == [[1.0, 0.0, 0.0]]
    assert data["rotation"] == [[0.0, 0.0, 0.0]]
    assert data["tool_state"] == ["home"]
    assert data["move_yaw_changes"] == [0.25, 0.5]
