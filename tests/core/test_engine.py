"""Headless engine tests (M3): full runs, stop semantics, failure paths."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.engine import (
    PHASE_ABOVE_EMBRYO,
    PHASE_ABOVE_MOVED,
    PHASE_GRASPED,
    PHASE_INITIAL,
    PHASE_RELEASED,
    EngineParams,
    FinishReason,
    SimulationEngine,
    Snapshot,
)
from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import Embryo, EmbryoState, ToolHead, ToolState, Workspace
from mrex_perception.core.setup import populate_random

HOME = np.array([15.0, 17.5, 10.0])


class _FixedRng:
    """Deterministic rng stub: ``random()`` always returns ``value``."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


def _workspace() -> Workspace:
    return load_workspace("default")


def _tool() -> ToolHead:
    return ToolHead.for_workspace(_workspace())


def _free(i: int, x: float, y: float) -> Embryo:
    return Embryo(id=i, position=np.array([x, y, 0.1]), orientation=rotation_z(0.0))


def test_completed_random_run_is_self_consistent() -> None:
    workspace = _workspace()
    rng = np.random.default_rng(42)
    embryos = populate_random(6, workspace, rng)
    engine = SimulationEngine(workspace, embryos, rng=rng, tool=_tool())

    result = engine.run()

    assert result.finish_reason == FinishReason.COMPLETED
    summary = result.summary
    assert summary is not None
    # accounting: every embryo ends in exactly one bucket (clustered is not in the report)
    clustered = sum(1 for e in result.embryos if e.state == EmbryoState.CLUSTERED)
    accounted = (
        summary.moved + summary.failed + summary.free + summary.selected + summary.grasped
    )
    assert accounted + clustered == summary.total == 6
    assert summary.free == 0  # the loop only ends once nothing is free
    # the tool returns home and the summary sees every recorded sample
    assert result.tool.state == ToolState.HOME
    assert result.tool.position == pytest.approx(HOME)
    assert summary.num_motion_samples == len(result.motion_log)
    assert result.motion_log.positions[0] == pytest.approx(HOME)


def test_deterministic_fixture_run_places_embryos_on_grid() -> None:
    workspace = _workspace()
    embryos = [_free(i + 1, x, 10.0) for i, x in enumerate([2.0, 4.0, 6.0])]
    engine = SimulationEngine(
        workspace, embryos, EngineParams(num_steps=4), rng=_FixedRng(0.0), tool=_tool()
    )

    result = engine.run()

    assert result.summary is not None
    assert result.summary.moved == 3
    assert result.summary.success_rate == pytest.approx(100.0)
    assert result.summary.total_attempts == 3
    assert all(e.state == EmbryoState.MOVED for e in result.embryos)
    # grid: spacing = length * movedSpacing = 2 -> x = 81, 83, 85; y = 6; z = 0.1
    assert sorted(e.position[0] for e in result.embryos) == pytest.approx([81.0, 83.0, 85.0])
    for embryo in result.embryos:
        assert embryo.position[1:] == pytest.approx([6.0, 0.1])
        assert embryo.orientation == pytest.approx(rotation_z(np.pi / 2), abs=1e-12)


def test_injected_tool_is_used_in_place() -> None:
    workspace = _workspace()
    embryos = [_free(1, 6.0, 10.0)]
    tool = ToolHead(position=np.array([20.0, 20.0, 12.0]), clearance=2.0)
    tool.home_position = tool.position.copy()
    tool.target_position = tool.position.copy()
    engine = SimulationEngine(
        workspace, embryos, EngineParams(num_steps=2), rng=_FixedRng(0.0), tool=tool
    )

    result = engine.run()

    # the injected instance is mutated in place and returned as-is
    assert result.tool is tool
    assert result.motion_log.positions[0] == pytest.approx([20.0, 20.0, 12.0])
    # approach target is embryo position + custom clearance -> [6, 10, 0.1 + 2.0]
    assert result.motion_log.positions[2] == pytest.approx([6.0, 10.0, 2.1])


def test_stop_mid_run_returns_stopped_without_home_or_summary() -> None:
    workspace = _workspace()
    embryos = [_free(1, 6.0, 10.0), _free(2, 4.0, 10.0)]
    holder: list[SimulationEngine] = []
    snapshots: list[Snapshot] = []

    def stop_after_seven_steps(snapshot: Snapshot) -> None:
        snapshots.append(snapshot)
        if snapshot.step_index >= 7 and not holder[0].stop_requested:
            holder[0].stop()

    engine = SimulationEngine(
        workspace,
        embryos,
        EngineParams(),
        rng=_FixedRng(0.0),
        tool=_tool(),
        on_step=stop_after_seven_steps,
    )
    holder.append(engine)
    result = engine.run()

    assert result.finish_reason == FinishReason.STOPPED
    assert result.summary is None
    # stopped runs never return home
    assert result.tool.state != ToolState.HOME
    # faithful MATLAB semantics: the interrupted iteration still grasps and
    # releases (the remaining moves break immediately), then the loop exits
    assert result.embryos[0].state == EmbryoState.MOVED
    assert result.embryos[1].state == EmbryoState.FREE
    assert len(result.motion_log) == 1 + 7 + 1 + 1  # initial + steps + grasp + release


def test_moved_region_full_raises() -> None:
    workspace = replace(_workspace(), moved_region=np.array([80.0, 5.0, 2.0, 2.0]))
    embryos = [_free(1, 6.0, 10.0), _free(2, 4.0, 10.0)]
    engine = SimulationEngine(
        workspace, embryos, EngineParams(num_steps=2), rng=_FixedRng(0.0), tool=_tool()
    )

    with pytest.raises(ValueError, match="Moved region is full"):
        engine.run()


def test_no_free_embryos_completes_with_empty_summary() -> None:
    workspace = _workspace()
    embryos = [_free(1, 5.0, 10.0), _free(2, 5.4, 10.0)]  # < 1 mm apart -> clustered
    engine = SimulationEngine(
        workspace, embryos, EngineParams(num_steps=5), rng=_FixedRng(0.0), tool=_tool()
    )

    result = engine.run()

    assert result.finish_reason == FinishReason.COMPLETED
    assert result.summary is not None
    assert result.summary.total == 2
    assert result.summary.moved == 0
    assert result.summary.free == 0
    assert all(e.state == EmbryoState.CLUSTERED for e in result.embryos)
    # faithful quirk: return_home still runs (no-op steps are recorded)
    assert len(result.motion_log) == 1 + 5
    assert result.tool.state == ToolState.HOME


def test_phase_and_step_hooks_emit_deep_copies() -> None:
    workspace = _workspace()
    embryos = [_free(1, 6.0, 10.0)]
    phases: list[str] = []
    snapshots: list[Snapshot] = []
    engine = SimulationEngine(
        workspace,
        embryos,
        EngineParams(num_steps=3),
        rng=_FixedRng(0.0),
        tool=_tool(),
        on_phase=phases.append,
        on_step=snapshots.append,
    )

    result = engine.run()

    assert phases == [
        PHASE_INITIAL,
        PHASE_ABOVE_EMBRYO,
        PHASE_GRASPED,
        PHASE_ABOVE_MOVED,
        PHASE_RELEASED,
    ]
    # 1 initial + 3 approach steps + 1 phase + 1 phase + 3 final steps
    # + 1 phase + 1 phase + 3 home steps
    assert len(snapshots) == 14
    assert snapshots[0].phase == PHASE_INITIAL
    assert snapshots[0].tool.position == pytest.approx(HOME)
    assert snapshots[0].embryos[0].state == EmbryoState.FREE
    assert snapshots[-1].step_index == 9  # 3 + 3 + 3 recorded steps

    # deep copies: mutating a snapshot leaks into neither later snapshots nor the result
    second_tool = snapshots[1].tool.position.copy()
    second_embryo = snapshots[1].embryos[0].position.copy()
    snapshots[0].tool.position[0] = 999.0
    snapshots[0].embryos[0].position[0] = 999.0
    assert snapshots[1].tool.position == pytest.approx(second_tool)
    assert snapshots[1].embryos[0].position == pytest.approx(second_embryo)
    assert result.embryos[0].position[0] == pytest.approx(81.0)  # engine state untouched
    assert result.tool.position == pytest.approx(HOME)
