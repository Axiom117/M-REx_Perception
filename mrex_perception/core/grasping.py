"""Grasp and release logic (ports of ``src/grasping/*.m``).

Randomness and hardware are injected: ``rng`` (any object with
``random() -> float``, normally ``np.random.Generator``) and ``pump`` (``None``
in simulation; a pump adapter with ``stop()`` / ``dispense(volume)`` in
hardware mode, M6). Simulation mode must never perform real waits.
"""

from __future__ import annotations

import warnings
from typing import Protocol

import numpy as np

from mrex_perception.core.math_ops import rotation_z
from mrex_perception.core.models import Embryo, ToolHead
from mrex_perception.core.states import EmbryoState, ToolState


class Pump(Protocol):
    """Minimal pump surface consumed by grasping (implemented in M6)."""

    def stop(self) -> None: ...

    def dispense(self, volume: float) -> None: ...


class RandomSource(Protocol):
    """Minimal RNG surface (``np.random.Generator`` satisfies it)."""

    def random(self) -> float: ...


def pickup_probability(embryo: Embryo) -> float:
    """Success probability of the next grasp (port of ``pickupModel.m``).

    ``p = 0.7 * (width / 0.2) - 0.05 * attempts``, clamped to [0, 1]. Note
    ``attempts`` is read after the caller incremented it (MATLAB order).
    """
    base_probability = 0.7
    contact_factor = embryo.width / 0.2
    attempt_penalty = 0.05 * embryo.attempts
    probability = base_probability * contact_factor - attempt_penalty
    return float(np.clip(probability, 0.0, 1.0))


def grasp(
    embryos: list[Embryo],
    tool: ToolHead,
    rng: RandomSource,
    pump: Pump | None = None,
) -> None:
    """Attempt to grasp the selected embryo (port of ``graspEmbryo.m``).

    Increments ``attempts`` first, then draws ``rng.random() <
    pickup_probability(...)`` (strict ``<``). On success both embryo and tool
    become ``grasped``; on failure the tool becomes ``failedGrasp`` and the
    embryo is ``failed`` at ``attempts >= 3``, otherwise ``free`` again. In
    hardware mode the pump is stopped before the attempt.
    """
    selected = next((e for e in embryos if e.state == EmbryoState.SELECTED), None)
    if selected is None:
        warnings.warn("No selected embryo found", stacklevel=2)
        return

    if pump is not None:
        pump.stop()

    selected.attempts += 1

    if rng.random() < pickup_probability(selected):
        tool.has_embryo = True
        tool.attached_embryo_id = selected.id
        tool.state = ToolState.GRASPED
        selected.state = EmbryoState.GRASPED
        selected.picked_successfully = True
    else:
        tool.has_embryo = False
        tool.attached_embryo_id = 0
        tool.state = ToolState.FAILED_GRASP
        if selected.attempts >= 3:
            selected.state = EmbryoState.FAILED
        else:
            selected.state = EmbryoState.FREE


def release(
    embryos: list[Embryo],
    tool: ToolHead,
    moved_position: np.ndarray,
    pump: Pump | None = None,
) -> None:
    """Release the attached embryo at ``moved_position`` (``releaseEmbryo.m``).

    Fixed final yaw of pi/2; embryo becomes ``moved``, tool becomes
    ``released`` with no attachment. The pump dispenses 2.7 (ml) only in
    hardware mode (``releaseWithPump(pump, 2.7)``).
    """
    attached_id = tool.attached_embryo_id
    if attached_id == 0:
        warnings.warn("No embryo attached", stacklevel=2)
        return

    if pump is not None:
        pump.dispense(2.7)

    embryo = embryos[attached_id - 1]
    embryo.orientation = rotation_z(np.pi / 2)
    embryo.position = np.array(moved_position, dtype=float)
    embryo.state = EmbryoState.MOVED

    tool.has_embryo = False
    tool.attached_embryo_id = 0
    tool.state = ToolState.RELEASED
