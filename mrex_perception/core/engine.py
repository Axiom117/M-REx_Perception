from __future__ import annotations

import copy
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np

from mrex_perception.core.models import Embryo, ToolHead, Workspace
from mrex_perception.core.reporting import SummaryReport, compute_summary
from mrex_perception.core.setup import mark_clustered
from mrex_perception.core.sim import (
    MotionLog,
    Pump,
    RngLike,
    grasp,
    has_free_embryos,
    move_tool_final,
    move_tool_to_embryo,
    next_moved_position,
    raise_tool,
    release,
    return_home,
    select_nearest_free,
)

PHASE_INITIAL = "Initial workspace"
PHASE_ABOVE_EMBRYO = "Tool above selected embryo"
PHASE_GRASPED = "Embryo grasped"
PHASE_ABOVE_MOVED = "Tool above moved position"
PHASE_RELEASED = "Embryo released"


class FinishReason(StrEnum):
    """How a run ended."""

    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass(eq=False)
class EngineParams:
    """Engine loop parameters (the script values of ``runSimulation.m``)."""

    num_steps: int = 50
    target_point: np.ndarray = field(default_factory=lambda: np.array([50.0, 50.0, 0.1]))
    phase_hold_seconds: float = 0.2  # presentation hint only; the engine never sleeps


@dataclass(eq=False)
class Snapshot:
    """Deep-copied simulation state for rendering (Qt-free, thread-safe)."""

    phase: str
    step_index: int  # cumulative interpolation steps recorded so far
    embryos: list[Embryo]
    tool: ToolHead


@dataclass(eq=False)
class EngineResult:
    """Final state of a run (``summary`` is ``None`` when stopped, per MATLAB)."""

    finish_reason: FinishReason
    summary: SummaryReport | None
    embryos: list[Embryo]
    tool: ToolHead
    motion_log: MotionLog


class SimulationEngine:
    def __init__(
        self,
        workspace: Workspace,
        embryos: list[Embryo],
        params: EngineParams | None = None,
        *,
        rng: RngLike,
        tool: ToolHead,
        pump: Pump | None = None,
        on_phase: Callable[[str], None] | None = None,
        on_step: Callable[[Snapshot], None] | None = None,
    ) -> None:
        self._workspace = workspace
        self._embryos = embryos
        self._params = params if params is not None else EngineParams()
        self._rng = rng
        self._pump = pump
        self._tool = tool
        self._on_phase = on_phase
        self._on_step = on_step
        self._motion_log = MotionLog()
        self._step_index = 0
        self._phase = PHASE_INITIAL
        self._stop_event = threading.Event()

    # -- control -------------------------------------------------------------

    def stop(self) -> None:
        """Request a stop (thread-safe; observed at the next loop/step check)."""
        self._stop_event.set()

    @property
    def stop_requested(self) -> bool:
        """True once :meth:`stop` has been called."""
        return self._stop_event.is_set()

    # -- main loop -------------------------------------------------------------

    def run(self) -> EngineResult:
        """Run the simulation to completion and return its final state."""
        mark_clustered(self._embryos)
        self._motion_log.record(self._tool)  # record the initial pose
        self._set_phase(PHASE_INITIAL)

        while has_free_embryos(self._embryos) and not self.stop_requested:
            select_nearest_free(self._embryos, self._params.target_point)
            self._move(move_tool_to_embryo)
            self._set_phase(PHASE_ABOVE_EMBRYO)

            grasp(self._embryos, self._tool, self._rng, self._pump)
            self._motion_log.record(self._tool)

            if not self._tool.has_embryo:
                self._move(raise_tool)
                continue

            self._set_phase(PHASE_GRASPED)
            moved_position = next_moved_position(self._embryos, self._workspace)
            self._move(move_tool_final, moved_position)
            self._set_phase(PHASE_ABOVE_MOVED)

            release(self._embryos, self._tool, moved_position, self._pump)
            self._motion_log.record(self._tool)
            self._set_phase(PHASE_RELEASED)

        if self.stop_requested:
            # A stopped run never returns home and produces no summary (MATLAB semantics).
            return EngineResult(
                FinishReason.STOPPED, None, self._embryos, self._tool, self._motion_log
            )

        self._move(return_home)
        summary = compute_summary(self._embryos, self._motion_log)
        return EngineResult(
            FinishReason.COMPLETED, summary, self._embryos, self._tool, self._motion_log
        )

    # -- motion / hooks / snapshots ----------------------------------------------

    def _move(self, move: Callable[..., None], *extra: object) -> None:
        """Run a ``sim`` motion helper wired to this run's log, stop signal and step hook."""
        move(
            self._embryos,
            self._tool,
            self._params.num_steps,
            self._motion_log,
            *extra,
            stop_token=self._stop_event,
            on_step=self._handle_step,
        )

    def _handle_step(self) -> None:
        self._step_index += 1
        self._publish()

    def _set_phase(self, title: str) -> None:
        self._phase = title
        if self._on_phase is not None:
            self._on_phase(title)
        self._publish()

    def _publish(self) -> None:
        if self._on_step is None:
            return
        self._on_step(
            Snapshot(
                phase=self._phase,
                step_index=self._step_index,
                embryos=copy.deepcopy(self._embryos),
                tool=copy.deepcopy(self._tool),
            )
        )
