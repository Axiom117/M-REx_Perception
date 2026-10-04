"""Headless simulation engine: the ``runSimulation.m`` main loop as a class.

``SimulationEngine`` owns the orchestration, while every behavior (planning,
motion, grasping, summary) stays in :mod:`mrex_perception.core.sim` /
:mod:`mrex_perception.core.reporting`. The engine is Qt-free and I/O-free:
callers supply the workspace and embryos, and observe the run through hooks.

Hooks (all optional):

- ``on_phase(title)`` — a new phase title is shown (the strings match
  ``runSimulation.m`` / ``updateSimulation`` exactly). ``EngineParams.
  phase_hold_seconds`` is only a presentation hint; the engine never sleeps.
- ``on_step(snapshot)`` — emitted after every recorded interpolation sample
  and at every phase change, with deep copies of the current state
  (:class:`Snapshot`), safe to hand to another thread (UI worker).

Stop semantics (faithful port, see migration plan §16): a stop request is only
observed at the top of the main loop and inside ``move_tool``'s per-step
check. A request arriving mid-move therefore completes the current iteration
(remaining moves break immediately, but grasp/release still run), after which
``FinishReason.STOPPED`` is returned without returning home and without a
summary. Instances are single-use: callers create a new engine per run.

This module lives at the top of ``core`` and orchestrates the layers below;
it never touches Qt, VTK or the file system itself.
"""

from __future__ import annotations

import copy
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np

from mrex_perception.core.models import Embryo, ToolHead, Workspace
from mrex_perception.core.reporting import SummaryReport, compute_summary
from mrex_perception.core.setup import create_tool_head, mark_clustered
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
    """Step-by-step port of the ``runSimulation.m`` while-loop."""

    def __init__(
        self,
        workspace: Workspace,
        embryos: list[Embryo],
        params: EngineParams | None = None,
        *,
        rng: RngLike,
        pump: Pump | None = None,
        on_phase: Callable[[str], None] | None = None,
        on_step: Callable[[Snapshot], None] | None = None,
    ) -> None:
        self._workspace = workspace
        self._embryos = embryos
        self._params = params if params is not None else EngineParams()
        self._rng = rng
        self._pump = pump
        self._on_phase = on_phase
        self._on_step = on_step
        self._tool: ToolHead | None = None
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
        tool = create_tool_head(self._workspace)
        self._tool = tool
        self._motion_log.record(tool)  # MATLAB records the initial pose
        self._set_phase(PHASE_INITIAL)

        while has_free_embryos(self._embryos):
            if self._stop_event.is_set():
                break

            select_nearest_free(self._embryos, self._params.target_point)
            move_tool_to_embryo(
                self._embryos, tool, self._params.num_steps, self._motion_log, **self._hooks()
            )
            self._set_phase(PHASE_ABOVE_EMBRYO)

            grasp(self._embryos, tool, self._rng, self._pump)
            self._motion_log.record(tool)

            if not tool.has_embryo:
                raise_tool(
                    self._embryos, tool, self._params.num_steps, self._motion_log, **self._hooks()
                )
                continue

            self._set_phase(PHASE_GRASPED)
            moved_position = next_moved_position(self._embryos, self._workspace)
            move_tool_final(
                self._embryos,
                tool,
                self._params.num_steps,
                moved_position,
                self._motion_log,
                **self._hooks(),
            )
            self._set_phase(PHASE_ABOVE_MOVED)

            release(self._embryos, tool, moved_position, self._pump)
            self._motion_log.record(tool)
            self._set_phase(PHASE_RELEASED)

        if self._stop_event.is_set():
            return EngineResult(
                FinishReason.STOPPED, None, self._embryos, tool, self._motion_log
            )

        return_home(
            self._embryos, tool, self._params.num_steps, self._motion_log, **self._hooks()
        )
        summary = compute_summary(self._embryos, self._motion_log)
        return EngineResult(
            FinishReason.COMPLETED, summary, self._embryos, tool, self._motion_log
        )

    # -- hooks / snapshots -------------------------------------------------------

    def _hooks(self) -> dict[str, Any]:
        """Common keyword arguments for the injected ``move_tool`` hooks."""
        return {"stop_token": self._stop_event, "on_step": self._handle_step}

    def _handle_step(self) -> None:
        self._step_index += 1
        self._publish()

    def _set_phase(self, title: str) -> None:
        self._phase = title
        if self._on_phase is not None:
            self._on_phase(title)
        self._publish()

    def _publish(self) -> None:
        if self._on_step is None or self._tool is None:
            return
        self._on_step(
            Snapshot(
                phase=self._phase,
                step_index=self._step_index,
                embryos=copy.deepcopy(self._embryos),
                tool=copy.deepcopy(self._tool),
            )
        )
