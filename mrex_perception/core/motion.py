"""Tool motion interpolation (ports of ``src/motion/*.m``).

``move_tool`` replaces the MATLAB couplings with injected hooks so the core
layer stays UI-free: ``stop_token`` (checked once per interpolation step,
mirroring ``simulationStopped``) and ``on_step`` (called after each sample is
recorded, where MATLAB called ``updateSimulation``).

All functions mutate ``embryos`` / ``tool`` in place and append to the passed
``MotionLog``; MATLAB's value-based ``[embryos, tool, motionLog]`` returns
become in-place updates. ID convention: ``tool.attached_embryo_id`` is 1-based
and indexes ``embryos[id - 1]`` (migration plan §9.3).

``lower_tool`` / ``lower_tool_moved`` are the corrected-semantics ports of the
never-working MATLAB legacy files (argument mix-up + typo, see §16-②); they
are kept for fidelity but are not wired into the engine.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Protocol

import numpy as np
from numpy.typing import ArrayLike

from mrex_perception.core.math_ops import rotation_z
from mrex_perception.core.models import Embryo, ToolHead
from mrex_perception.core.motion_log import MotionLog
from mrex_perception.core.states import EmbryoState, ToolState


class StopToken(Protocol):
    """Minimal stop-signal surface (``threading.Event`` satisfies it)."""

    def is_set(self) -> bool: ...


def resolve_target_yaw(target_rotation: float | int | np.ndarray) -> float:
    """Return the target yaw from either a scalar angle or a 3x3 matrix.

    Mirrors the ``isscalar`` / ``[3, 3]`` check in ``moveTool.m``; anything
    else raises the same class of error.
    """
    arr = np.asarray(target_rotation, dtype=float)
    if arr.ndim == 0 or arr.size == 1:
        return float(arr.reshape(-1)[0])
    if arr.shape == (3, 3):
        return float(np.arctan2(arr[1, 0], arr[0, 0]))
    raise ValueError("targetRotation must be a scalar yaw angle or a 3-by-3 rotation matrix.")


def _find_selected(embryos: list[Embryo]) -> Embryo | None:
    return next((e for e in embryos if e.state == EmbryoState.SELECTED), None)


def move_tool(
    embryos: list[Embryo],
    tool: ToolHead,
    target_position: ArrayLike,
    target_rotation: float | int | np.ndarray,
    num_steps: int,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Interpolate the tool to a target pose over ``num_steps`` steps.

    Port of ``moveTool.m``: linear position interpolation, shortest-angle yaw
    interpolation (``wrap_to_pi``), attached-embryo following, per-step stop
    check and logging. Returns early only via ``stop_token``.
    """
    start_position = np.array(tool.position, dtype=float)
    start_rotation = np.array(tool.orientation, dtype=float)
    start_yaw = float(np.arctan2(start_rotation[1, 0], start_rotation[0, 0]))
    target_yaw = resolve_target_yaw(target_rotation)

    # shortest angular movement (wrap to [-pi, pi])
    yaw_difference = float(
        np.arctan2(np.sin(target_yaw - start_yaw), np.cos(target_yaw - start_yaw))
    )
    motion_log.record_move_yaw_change(abs(yaw_difference))

    target_position = np.array(target_position, dtype=float)

    for k in range(1, num_steps + 1):
        if stop_token is not None and stop_token.is_set():
            break

        alpha = k / num_steps

        tool.position = (1.0 - alpha) * start_position + alpha * target_position

        current_yaw = start_yaw + alpha * yaw_difference
        tool.orientation = rotation_z(current_yaw)

        if tool.has_embryo:
            if tool.attached_embryo_id < 1:
                raise ValueError("has_embryo is set but attached_embryo_id is 0")
            embryo = embryos[tool.attached_embryo_id - 1]
            embryo.position = tool.position - np.array([0.0, 0.0, tool.clearance])
            embryo.orientation = tool.orientation.copy()

        motion_log.record(tool)
        if on_step is not None:
            on_step()

    tool.target_position = target_position


def move_tool_to_embryo(
    embryos: list[Embryo],
    tool: ToolHead,
    num_steps: int,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Move above the selected embryo; set ``aboveEmbryo`` (``moveToolToEmbryo.m``)."""
    selected = _find_selected(embryos)
    if selected is None:
        warnings.warn("No selected embryo found", stacklevel=2)
        return

    target_position = selected.position + np.array([0.0, 0.0, tool.clearance])
    move_tool(
        embryos,
        tool,
        target_position,
        selected.orientation,
        num_steps,
        motion_log,
        stop_token=stop_token,
        on_step=on_step,
    )
    tool.state = ToolState.ABOVE_EMBRYO


def move_tool_final(
    embryos: list[Embryo],
    tool: ToolHead,
    num_steps: int,
    moved_position: ArrayLike,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Move above the drop-off position keeping orientation (``moveToolFinal.m``)."""
    if tool.attached_embryo_id == 0:
        warnings.warn("Tool has no attached embryo", stacklevel=2)
        return

    target_position = np.asarray(moved_position, dtype=float) + np.array(
        [0.0, 0.0, tool.clearance]
    )
    move_tool(
        embryos,
        tool,
        target_position,
        tool.orientation,
        num_steps,
        motion_log,
        stop_token=stop_token,
        on_step=on_step,
    )
    tool.state = ToolState.ABOVE_MOVED_POSITION


def raise_tool(
    embryos: list[Embryo],
    tool: ToolHead,
    num_steps: int,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Raise by one clearance keeping orientation; set ``lifted`` (``raiseTool.m``)."""
    target_position = tool.position + np.array([0.0, 0.0, tool.clearance])
    move_tool(
        embryos,
        tool,
        target_position,
        tool.orientation,
        num_steps,
        motion_log,
        stop_token=stop_token,
        on_step=on_step,
    )
    tool.state = ToolState.LIFTED


def return_home(
    embryos: list[Embryo],
    tool: ToolHead,
    num_steps: int,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Move to the home position and identity orientation (``returnHome.m``)."""
    move_tool(
        embryos,
        tool,
        tool.home_position,
        np.eye(3),
        num_steps,
        motion_log,
        stop_token=stop_token,
        on_step=on_step,
    )
    tool.state = ToolState.HOME


def lower_tool(
    embryos: list[Embryo],
    tool: ToolHead,
    num_steps: int,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Legacy (not wired into the engine): lower onto the selected embryo.

    Corrected-semantics port of ``lowerTool.m`` (the MATLAB version mixed up
    arguments and referenced a misspelled variable, so it never ran); the
    intended target is ``position + [0, 0, embryo.height + tool.height]``.
    """
    selected = _find_selected(embryos)
    if selected is None:
        warnings.warn("No embryo found", stacklevel=2)
        return

    target_position = selected.position + np.array([0.0, 0.0, selected.height + tool.height])
    move_tool(
        embryos,
        tool,
        target_position,
        tool.orientation,
        num_steps,
        motion_log,
        stop_token=stop_token,
        on_step=on_step,
    )
    tool.state = ToolState.CONTACT


def lower_tool_moved(
    embryos: list[Embryo],
    tool: ToolHead,
    num_steps: int,
    moved_position: ArrayLike,
    motion_log: MotionLog,
    *,
    stop_token: StopToken | None = None,
    on_step: Callable[[], None] | None = None,
) -> None:
    """Legacy (not wired into the engine): lower onto the drop-off position.

    Corrected-semantics port of ``lowerToolMoved.m`` (same argument mix-up as
    ``lowerTool.m``); target is ``moved_position + [0, 0, tool.height]``.
    """
    target_position = np.asarray(moved_position, dtype=float) + np.array([0.0, 0.0, tool.height])
    move_tool(
        embryos,
        tool,
        target_position,
        tool.orientation,
        num_steps,
        motion_log,
        stop_token=stop_token,
        on_step=on_step,
    )
    tool.state = ToolState.PLACE_CONTACT
