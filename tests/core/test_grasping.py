"""Grasp / release logic (M2)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import Embryo, EmbryoState, ToolHead, ToolState
from mrex_perception.core.sim import grasp, pickup_probability, release


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


def test_pickup_probability() -> None:
    assert pickup_probability(Embryo(id=1)) == pytest.approx(0.7)
    assert pickup_probability(_selected(attempts=1)) == pytest.approx(0.65)
    assert pickup_probability(_selected(attempts=5)) == pytest.approx(0.45)
    assert pickup_probability(Embryo(id=1, width=0.1)) == pytest.approx(0.35)
    # clamped to [0, 1]
    assert pickup_probability(Embryo(id=1, width=0.4)) == pytest.approx(1.0)
    assert pickup_probability(_selected(attempts=20)) == pytest.approx(0.0)


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


def test_grasp_failure_paths() -> None:
    # first failure: embryo goes back to free
    embryo = _selected(attempts=0)
    tool = ToolHead()
    grasp([embryo], tool, _FixedRng(1.0), None)
    assert embryo.attempts == 1
    assert embryo.state == EmbryoState.FREE
    assert not embryo.picked_successfully
    assert not tool.has_embryo
    assert tool.attached_embryo_id == 0
    assert tool.state == ToolState.FAILED_GRASP

    # third failure: failed for good
    embryo = _selected(attempts=2)
    grasp([embryo], tool, _FixedRng(1.0), None)
    assert embryo.attempts == 3
    assert embryo.state == EmbryoState.FAILED

    # success test is strict `<`: a draw equal to the probability still fails
    embryo = _selected(attempts=0)  # probability after increment = 0.7 - 0.05 = 0.65
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


def test_release() -> None:
    other = _selected(i=1)
    embryo = _selected(i=2, attempts=1)
    embryo.state = EmbryoState.GRASPED
    tool = ToolHead(has_embryo=True, attached_embryo_id=2, state=ToolState.GRASPED)
    moved = np.array([81.0, 6.0, 0.1])
    pump = _RecordingPump()

    release([other, embryo], tool, moved, pump)  # hardware mode dispenses 2.7

    assert embryo.state == EmbryoState.MOVED
    assert embryo.position == pytest.approx(moved)
    assert embryo.orientation == pytest.approx(rotation_z(np.pi / 2), abs=1e-12)
    assert not tool.has_embryo
    assert tool.attached_embryo_id == 0
    assert tool.state == ToolState.RELEASED
    assert pump.calls == [("dispense", 2.7)]

    # no attachment -> warn, unchanged
    loose = ToolHead()
    with pytest.warns(UserWarning, match="No embryo attached"):
        release([_selected()], loose, np.zeros(3), None)
    assert loose.state == ToolState.HOME
