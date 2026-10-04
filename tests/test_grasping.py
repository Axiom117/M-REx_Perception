"""Grasp / release logic (M2)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.core.grasping import grasp, pickup_probability, release
from mrex_perception.core.math_ops import rotation_z
from mrex_perception.core.models import Embryo, ToolHead
from mrex_perception.core.states import EmbryoState, ToolState


class _FixedRng:
    """Deterministic rng stub: ``random()`` always returns ``value``."""

    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


class _RecordingPump:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float | None]] = []

    def stop(self) -> None:
        self.calls.append(("stop", None))

    def dispense(self, volume: float) -> None:
        self.calls.append(("dispense", volume))


def _selected(i: int = 1, attempts: int = 0, width: float = 0.2) -> Embryo:
    return Embryo(id=i, state=EmbryoState.SELECTED, attempts=attempts, width=width)


# -- pickup_probability ------------------------------------------------------


def test_pickup_probability_formula() -> None:
    assert pickup_probability(Embryo(id=1)) == pytest.approx(0.7)
    assert pickup_probability(_selected(attempts=1)) == pytest.approx(0.65)
    assert pickup_probability(_selected(attempts=5)) == pytest.approx(0.45)
    assert pickup_probability(Embryo(id=1, width=0.1)) == pytest.approx(0.35)


def test_pickup_probability_is_clamped() -> None:
    assert pickup_probability(Embryo(id=1, width=0.4)) == pytest.approx(1.0)
    assert pickup_probability(_selected(attempts=20)) == pytest.approx(0.0)


# -- grasp -------------------------------------------------------------------


def test_grasp_success() -> None:
    embryo = _selected()
    tool = ToolHead()

    grasp([embryo], tool, _FixedRng(0.0), None)

    assert embryo.attempts == 1
    assert embryo.state == EmbryoState.GRASPED
    assert embryo.picked_successfully
    assert tool.has_embryo
    assert tool.attached_embryo_id == 1
    assert tool.state == ToolState.GRASPED


def test_grasp_failure_below_three_attempts_frees_embryo() -> None:
    embryo = _selected(attempts=0)
    tool = ToolHead()

    grasp([embryo], tool, _FixedRng(1.0), None)

    assert embryo.attempts == 1
    assert embryo.state == EmbryoState.FREE
    assert not embryo.picked_successfully
    assert not tool.has_embryo
    assert tool.attached_embryo_id == 0
    assert tool.state == ToolState.FAILED_GRASP


def test_grasp_failure_third_attempt_fails_embryo() -> None:
    embryo = _selected(attempts=2)
    tool = ToolHead()

    grasp([embryo], tool, _FixedRng(1.0), None)

    assert embryo.attempts == 3
    assert embryo.state == EmbryoState.FAILED


def test_grasp_success_is_strict_less_than_probability() -> None:
    # probability after increment is 0.7 - 0.05 = 0.65; draw equal -> failure
    embryo = _selected(attempts=0)
    tool = ToolHead()

    grasp([embryo], tool, _FixedRng(0.7 - 0.05), None)

    assert embryo.state == EmbryoState.FREE
    assert tool.state == ToolState.FAILED_GRASP


def test_grasp_warns_without_selected() -> None:
    embryo = Embryo(id=1)
    tool = ToolHead()

    with pytest.warns(UserWarning, match="No selected embryo found"):
        grasp([embryo], tool, _FixedRng(0.0), None)

    assert embryo.attempts == 0
    assert tool.state == ToolState.HOME


def test_grasp_stops_pump_first_in_hardware_mode() -> None:
    embryo = _selected()
    tool = ToolHead()
    pump = _RecordingPump()

    grasp([embryo], tool, _FixedRng(0.0), pump)

    assert pump.calls == [("stop", None)]


# -- release -----------------------------------------------------------------


def test_release_resets_embryo_and_tool() -> None:
    other = _selected(i=1)
    embryo = _selected(i=2, attempts=1)
    embryo.state = EmbryoState.GRASPED
    tool = ToolHead(has_embryo=True, attached_embryo_id=2, state=ToolState.GRASPED)
    moved = np.array([81.0, 6.0, 0.1])

    release([other, embryo], tool, moved, None)

    assert embryo.state == EmbryoState.MOVED
    assert embryo.position == pytest.approx(moved)
    assert embryo.orientation == pytest.approx(rotation_z(np.pi / 2), abs=1e-12)
    assert not tool.has_embryo
    assert tool.attached_embryo_id == 0
    assert tool.state == ToolState.RELEASED


def test_release_warns_without_attached_embryo() -> None:
    tool = ToolHead()

    with pytest.warns(UserWarning, match="No embryo attached"):
        release([_selected()], tool, np.zeros(3), None)

    assert tool.state == ToolState.HOME


def test_release_dispenses_2_7_only_in_hardware_mode() -> None:
    embryo = _selected(i=1)
    embryo.state = EmbryoState.GRASPED
    tool = ToolHead(has_embryo=True, attached_embryo_id=1)
    pump = _RecordingPump()

    release([embryo], tool, np.array([81.0, 6.0, 0.1]), pump)

    assert pump.calls == [("dispense", 2.7)]
