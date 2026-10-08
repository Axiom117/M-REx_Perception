"""Simulation worker thread: runs the engine off the UI thread.

The engine calls ``on_step`` for every recorded interpolation sample (and phase
change); the worker stores each deep-copied snapshot in a lock-protected slot
that the UI polls at its own pace (latest-wins), paces the run for animation,
and implements pause / single-step / stop on that hook. The worker never
touches widgets: results travel through signals only.
"""

from __future__ import annotations

import threading
import time
import traceback

from PySide6.QtCore import QThread, Signal

from mrex_perception.core.engine import EngineParams, SimulationEngine, Snapshot
from mrex_perception.core.models import Embryo, ToolHead, Workspace
from mrex_perception.core.sim import Pump, RngLike

STEP_DELAY_SECONDS = 1 / 60  # animation pace: one recorded step per frame


class SimulationWorker(QThread):
    """One engine run; ``runFinished`` carries the ``EngineResult``, ``failed`` a message."""

    runFinished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        workspace: Workspace,
        embryos: list[Embryo],
        params: EngineParams,
        *,
        rng: RngLike,
        tool: ToolHead,
        pump: Pump | None = None,
        cluster_threshold: float = 1.0,
        step_delay: float = STEP_DELAY_SECONDS,
    ) -> None:
        super().__init__()
        self._workspace = workspace
        self._embryos = embryos
        self._params = params
        self._rng = rng
        self._tool = tool
        self._pump = pump
        self._cluster_threshold = cluster_threshold
        self._step_delay = step_delay

        self._engine: SimulationEngine | None = None
        self._snapshot_lock = threading.Lock()
        self._snapshot: Snapshot | None = None
        self._gate = threading.Condition()
        self._paused = False
        self._stepping = False

    # -- UI-thread API -------------------------------------------------------

    def take_snapshot(self) -> Snapshot | None:
        """Latest published snapshot (immutable after publish; read-only for the UI)."""
        with self._snapshot_lock:
            return self._snapshot

    def request_pause(self, paused: bool) -> None:
        with self._gate:
            self._paused = paused
            if paused:
                self._stepping = False
            self._gate.notify_all()

    def request_step(self) -> None:
        """Release exactly one pending step while paused."""
        with self._gate:
            self._stepping = True
            self._gate.notify_all()

    def request_stop(self) -> None:
        with self._gate:
            if self._engine is not None:
                self._engine.stop()
            self._gate.notify_all()

    # -- worker thread -------------------------------------------------------

    def run(self) -> None:
        engine = SimulationEngine(
            self._workspace,
            self._embryos,
            self._params,
            rng=self._rng,
            tool=self._tool,
            pump=self._pump,
            cluster_threshold=self._cluster_threshold,
            on_step=self._on_step,
        )
        with self._gate:
            self._engine = engine
        try:
            result = engine.run()
        except Exception:  # noqa: BLE001 - any failure is reported to the UI as text
            self.failed.emit(traceback.format_exc())
            return
        self.runFinished.emit(result)

    def _on_step(self, snapshot: Snapshot) -> None:
        with self._snapshot_lock:
            self._snapshot = snapshot
        self._wait_if_paused()
        if self._step_delay > 0:
            time.sleep(self._step_delay)

    def _wait_if_paused(self) -> None:
        with self._gate:
            while True:
                if self._stop_requested():
                    return
                if not self._paused:
                    return
                if self._stepping:
                    self._stepping = False
                    return
                self._gate.wait()

    def _stop_requested(self) -> bool:
        return self._engine is not None and self._engine.stop_requested
