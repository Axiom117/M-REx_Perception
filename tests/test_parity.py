"""MATLAB/Python parity checks against ``tests/matlab/trace_m2.json`` (M2).

The trace is produced by ``tests/matlab/dumpFixture.m`` running the frozen
MATLAB reference implementation (``src/**``) on
``tests/fixtures/scenario_basic.json``::

    matlab -batch "cd tests/matlab; dumpFixture"

Deterministic outputs must match within 1e-9 (migration plan §9). Grasp
outcomes are replayed from the raw ``rand()`` values recorded in the trace.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.embryos import mark_clustered
from mrex_perception.core.grasping import grasp, release
from mrex_perception.core.math_ops import rotation_z
from mrex_perception.core.models import Embryo, ToolHead
from mrex_perception.core.motion import (
    move_tool,
    move_tool_final,
    move_tool_to_embryo,
    raise_tool,
    return_home,
)
from mrex_perception.core.motion_log import MotionLog
from mrex_perception.core.planner import next_moved_position, select_nearest_free
from mrex_perception.core.states import EmbryoState
from mrex_perception.core.summary import compute_summary
from mrex_perception.core.tool import create_tool_head

TESTS_DIR = Path(__file__).resolve().parent
TRACE_PATH = TESTS_DIR / "matlab" / "trace_m2.json"
FIXTURE_PATH = TESTS_DIR / "fixtures" / "scenario_basic.json"

ATOL = 1e-9

pytestmark = pytest.mark.skipif(
    not TRACE_PATH.exists(), reason="run tests/matlab/dumpFixture.m to create trace_m2.json"
)


@pytest.fixture(scope="module")
def trace() -> dict[str, Any]:
    return json.loads(TRACE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class _SeqRng:
    """Deterministic rng replaying the raw draws recorded by the dump."""

    def __init__(self, draws: Any) -> None:
        self.draws = np.atleast_1d(np.asarray(draws, dtype=float)).tolist()
        self.index = 0

    def random(self) -> float:
        value = self.draws[self.index]
        self.index += 1
        return value


def _allclose(actual: Any, expected: Any) -> None:
    np.testing.assert_allclose(
        np.asarray(actual, dtype=float), np.asarray(expected, dtype=float), rtol=0, atol=ATOL
    )


def _fixture_embryos(fixture: dict[str, Any]) -> list[Embryo]:
    return [
        Embryo(
            id=e["id"],
            state=EmbryoState(e["state"]),
            attempts=e["attempts"],
            picked_successfully=e["picked_successfully"],
            width=e["width"],
            length=e["length"],
            height=e["height"],
            confidence=e["confidence"],
            position=np.array(e["position"], dtype=float),
            orientation=rotation_z(e["yaw"]),
            is_clustered=e["is_clustered"],
        )
        for e in fixture["embryos"]
    ]


# -- A. single moveTool trajectory -------------------------------------------


def test_trajectory(trace: dict[str, Any]) -> None:
    case = trace["trajectory"]
    tool = ToolHead(position=np.array(case["startPosition"], dtype=float))
    log = MotionLog()

    move_tool([], tool, case["targetPosition"], case["targetYawRad"], case["numSteps"], log)

    _allclose(log.positions, case["positions"])
    _allclose(log.rotation, case["rotation"])
    assert log.tool_state.tolist() == case["toolState"]
    _allclose(log.move_yaw_changes, case["moveYawChanges"])
    _allclose(tool.target_position, case["finalTargetPosition"])


# -- B. shortest angle across +/-pi ------------------------------------------


def test_wrap_case(trace: dict[str, Any]) -> None:
    case = trace["wrapCase"]
    tool = ToolHead(
        position=np.zeros(3), orientation=rotation_z(case["startYawRad"])
    )
    log = MotionLog()

    move_tool([], tool, np.zeros(3), case["targetYawRad"], case["numSteps"], log)

    _allclose(log.rotation, case["rotation"])
    _allclose(log.move_yaw_changes, case["moveYawChanges"])


# -- C. attached embryo follows every step ------------------------------------


def test_follow_case(trace: dict[str, Any]) -> None:
    case = trace["followCase"]
    embryo = Embryo(
        id=1,
        position=np.array([5.0, 5.0, 0.1]),
        orientation=rotation_z(case["startYawRad"]),
    )
    tool = ToolHead(
        position=np.array(case["startPosition"], dtype=float),
        orientation=rotation_z(case["startYawRad"]),
    )
    tool.has_embryo = True
    tool.attached_embryo_id = 1
    log = MotionLog()

    tool_positions: list[np.ndarray] = []
    tool_orientations: list[np.ndarray] = []
    attached_positions: list[np.ndarray] = []
    attached_orientations: list[np.ndarray] = []

    def on_step() -> None:
        tool_positions.append(tool.position.copy())
        tool_orientations.append(tool.orientation.flatten(order="F"))
        attached_positions.append(embryo.position.copy())
        attached_orientations.append(embryo.orientation.flatten(order="F"))

    move_tool(
        [embryo],
        tool,
        case["targetPosition"],
        case["targetYawRad"],
        case["numSteps"],
        log,
        on_step=on_step,
    )

    _allclose(tool_positions, case["toolPositions"])
    _allclose(tool_orientations, case["toolOrientations"])
    _allclose(attached_positions, case["attachedPositions"])
    _allclose(attached_orientations, case["attachedOrientations"])
    _allclose(embryo.position, case["finalEmbryoPosition"])
    _allclose(embryo.orientation.flatten(order="F"), case["finalEmbryoOrientation"])


# -- D. moved-grid positions and capacity errors ------------------------------


def test_moved_grid_cases(trace: dict[str, Any]) -> None:
    ws = load_workspace("default")
    for case in trace["movedGrid"]["cases"]:
        embryos = [Embryo(id=i + 1) for i in range(50)]
        for embryo in embryos[: case["movedCount"]]:
            embryo.state = EmbryoState.MOVED
        position = next_moved_position(embryos, ws)
        _allclose(position, case["position"])


def test_moved_grid_errors(trace: dict[str, Any]) -> None:
    ws = load_workspace("default")
    for case in trace["movedGrid"]["errors"]:
        ws.moved_region = np.array(case["region"], dtype=float)
        embryos = [Embryo(id=i + 1) for i in range(50)]
        for embryo in embryos[: case["movedCount"]]:
            embryo.state = EmbryoState.MOVED
        with pytest.raises(ValueError) as excinfo:
            next_moved_position(embryos, ws)
        assert str(excinfo.value) == case["message"]


# -- E. grasp outcomes and release --------------------------------------------


def _grasp_pressure(attempts: int, width: float = 0.2) -> float:
    probability = 0.7 * (width / 0.2) - 0.05 * attempts
    return max(0.0, min(1.0, probability))


def test_grasp_success_case(trace: dict[str, Any], fixture: dict[str, Any]) -> None:
    case = trace["graspSuccess"]
    draws = np.atleast_1d(case["draws"])
    embryos = _fixture_embryos(fixture)
    embryos[0].state = EmbryoState.SELECTED
    tool = create_tool_head(load_workspace("default"))

    grasp(embryos, tool, _SeqRng(draws), None)

    assert case["toolHasEmbryo"]
    assert draws[0] < _grasp_pressure(case["attempts"])
    assert embryos[0].attempts == case["attempts"]
    assert str(embryos[0].state) == case["embryoState"]
    assert embryos[0].picked_successfully == case["pickedSuccessfully"]
    assert str(tool.state) == case["toolState"]
    assert tool.has_embryo == case["toolHasEmbryo"]
    assert tool.attached_embryo_id == case["toolAttachedID"]


def test_grasp_fail_one_case(trace: dict[str, Any], fixture: dict[str, Any]) -> None:
    case = trace["graspFailOne"]
    draws = np.atleast_1d(case["draws"])
    embryos = _fixture_embryos(fixture)
    embryos[0].state = EmbryoState.SELECTED
    tool = create_tool_head(load_workspace("default"))

    grasp(embryos, tool, _SeqRng(draws), None)

    assert not case["toolHasEmbryo"]
    assert draws[0] >= _grasp_pressure(case["attempts"])
    assert embryos[0].attempts == case["attempts"]
    assert str(embryos[0].state) == case["embryoState"]
    assert str(tool.state) == case["toolState"]
    assert not tool.has_embryo
    assert tool.attached_embryo_id == case["toolAttachedID"]


def test_grasp_fail_three_case(trace: dict[str, Any], fixture: dict[str, Any]) -> None:
    case = trace["graspFailThree"]
    embryos = _fixture_embryos(fixture)
    tool = create_tool_head(load_workspace("default"))
    rng = _SeqRng(case["draws"])

    for i, draw in enumerate(case["draws"]):
        # graspEmbryo sends a failed embryo back to "free"; the main loop
        # re-selects before every attempt, so mirror that here.
        embryos[0].state = EmbryoState.SELECTED
        grasp(embryos, tool, rng, None)
        assert draw >= _grasp_pressure(case["attempts"][i])
        assert embryos[0].attempts == case["attempts"][i]
        assert str(embryos[0].state) == case["embryoStates"][i]
        assert str(tool.state) == case["toolStates"][i]

    assert str(embryos[0].state) == case["finalEmbryoState"]


def test_release_case(trace: dict[str, Any], fixture: dict[str, Any]) -> None:
    case = trace["release"]
    # rebuild the post-success state exactly as the dump did
    embryos = _fixture_embryos(fixture)
    embryos[0].state = EmbryoState.SELECTED
    tool = create_tool_head(load_workspace("default"))
    grasp(embryos, tool, _SeqRng(trace["graspSuccess"]["draws"]), None)

    release(embryos, tool, np.array(case["movedPosition"], dtype=float), None)

    assert str(embryos[0].state) == case["embryoState"]
    _allclose(embryos[0].position, case["embryoPosition"])
    _allclose(embryos[0].orientation.flatten(order="F"), case["embryoOrientation"])
    assert str(tool.state) == case["toolState"]
    assert tool.has_embryo == case["toolHasEmbryo"]
    assert tool.attached_embryo_id == case["toolAttachedID"]


# -- F. full engine loop on the fixture ---------------------------------------


def test_engine_loop(trace: dict[str, Any], fixture: dict[str, Any]) -> None:
    loop = trace["engineLoop"]
    ws = load_workspace("default")
    embryos = mark_clustered(_fixture_embryos(fixture))
    tool = create_tool_head(ws)
    log = MotionLog()
    log.record(tool)

    target_point = np.array([50.0, 50.0, 0.1])
    num_steps = 50

    for iteration in loop["iterations"]:
        select_nearest_free(embryos, target_point)
        selected_index = next(
            i for i, e in enumerate(embryos) if e.state == EmbryoState.SELECTED
        )
        assert selected_index + 1 == iteration["selectedID"]

        move_tool_to_embryo(embryos, tool, num_steps, log)
        grasp(embryos, tool, _SeqRng([iteration["graspDraw"]]), None)
        log.record(tool)

        assert tool.has_embryo == iteration["graspSucceeded"]

        if not tool.has_embryo:
            raise_tool(embryos, tool, num_steps, log)
        else:
            moved = next_moved_position(embryos, ws)
            _allclose(moved, iteration["movedPosition"])
            move_tool_final(embryos, tool, num_steps, moved, log)
            release(embryos, tool, moved, None)
            log.record(tool)

        for embryo, expected_attempts, expected_state in zip(
            embryos, iteration["attemptsAfter"], iteration["embryoStatesAfter"], strict=True
        ):
            assert embryo.attempts == expected_attempts
            assert str(embryo.state) == expected_state

    return_home(embryos, tool, num_steps, log)

    # full motion log parity
    mat_log = loop["motionLog"]
    _allclose(log.positions, mat_log["positions"])
    _allclose(log.rotation, mat_log["rotation"])
    assert log.tool_state.tolist() == mat_log["toolState"]
    _allclose(log.move_yaw_changes, mat_log["moveYawChanges"])

    # final embryo/tool state parity
    final = loop["finalEmbryos"]
    assert [str(e.state) for e in embryos] == final["states"]
    assert [int(e.attempts) for e in embryos] == final["attempts"]
    assert [e.picked_successfully for e in embryos] == final["pickedSuccessfully"]
    _allclose(np.array([e.position for e in embryos]), final["positions"])
    _allclose(
        np.array([e.orientation.flatten(order="F") for e in embryos]), final["orientations"]
    )
    final_tool = loop["finalTool"]
    _allclose(tool.position, final_tool["position"])
    _allclose(tool.orientation.flatten(order="F"), final_tool["orientation"])
    assert str(tool.state) == final_tool["state"]

    # summary parity: every field of SummaryReport must match the MATLAB mirror
    report = compute_summary(embryos, log)
    report_dict = json.loads(json.dumps(report.to_dict()))
    mat_summary = loop["summary"]
    for key, value in report_dict.items():
        assert key in mat_summary, f"summary key missing from MATLAB trace: {key}"
        _allclose(value, mat_summary[key])
