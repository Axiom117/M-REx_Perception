"""Dashboard panel: run controls, source settings, telemetry and live charts.

The layout lives in ``dashboard.ui`` (edit it with Qt Designer); this module
wires behaviour: control signals for the window controller, run-state
switching, and live updates from engine snapshots / results.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from mrex_perception.core.engine import EngineResult, Snapshot
from mrex_perception.core.models import Embryo, EmbryoState
from mrex_perception.ui.charts import ChartRecorder

from .ui_dashboard import Ui_DashboardPanel


class DashboardPanel(QWidget):
    """Left-hand control panel + telemetry."""

    startRequested = Signal()
    pauseRequested = Signal()
    stepRequested = Signal()
    stopRequested = Signal()
    resetRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_DashboardPanel()
        self.ui.setupUi(self)
        self._charts = ChartRecorder(self.ui.zPlot, self.ui.yawPlot, self.ui.distancePlot)
        self._paused = False

        self.ui.startButton.clicked.connect(self.startRequested.emit)
        self.ui.pauseButton.clicked.connect(self.pauseRequested.emit)
        self.ui.stepButton.clicked.connect(self.stepRequested.emit)
        self.ui.stopButton.clicked.connect(self.stopRequested.emit)
        self.ui.resetButton.clicked.connect(self.resetRequested.emit)

        self.set_running(False)
        self.reset_display()

    # -- run parameters (read by the controller at start) --------------------

    @property
    def count(self) -> int:
        return self.ui.countSpin.value()

    @property
    def seed(self) -> int:
        return self.ui.seedSpin.value()

    @property
    def num_steps(self) -> int:
        return self.ui.numStepsSpin.value()

    @property
    def target_point(self) -> np.ndarray:
        return np.array(
            [
                self.ui.targetXSpin.value(),
                self.ui.targetYSpin.value(),
                self.ui.targetZSpin.value(),
            ]
        )

    # -- run-state handling (called by the controller) -----------------------

    def begin_run(self) -> None:
        self.reset_display()
        self.set_running(True)
        self.set_paused(False)

    def set_running(self, running: bool) -> None:
        ui = self.ui
        ui.startButton.setEnabled(not running)
        ui.resetButton.setEnabled(not running)
        ui.stopButton.setEnabled(running)
        ui.pauseButton.setEnabled(running)
        ui.stepButton.setEnabled(running and self._paused)
        for control in (
            ui.countSpin,
            ui.seedSpin,
            ui.numStepsSpin,
            ui.targetXSpin,
            ui.targetYSpin,
            ui.targetZSpin,
        ):
            control.setEnabled(not running)
        if not running:
            self.set_paused(False)

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self.ui.pauseButton.setText("Resume" if paused else "Pause")
        self.ui.stepButton.setEnabled(paused)

    # -- live updates --------------------------------------------------------

    def add_sample(self, snapshot: Snapshot) -> None:
        """Accumulate chart data for one snapshot (cheap; no repaint)."""
        self._charts.add(snapshot)

    def update_live(self, snapshot: Snapshot) -> None:
        """Refresh visible telemetry (labels + throttled chart redraw)."""
        ui = self.ui
        ui.toolStateLabel.setText(str(snapshot.tool.state))
        ui.progressLabel.setText(self._progress_text(snapshot.embryos))
        ui.attemptsLabel.setText(str(sum(e.attempts for e in snapshot.embryos)))
        ui.successLabel.setText(self._success_text(snapshot.embryos))
        self._charts.redraw()

    def finish(self, result: EngineResult) -> None:
        ui = self.ui
        ui.progressLabel.setText(self._progress_text(result.embryos))
        ui.attemptsLabel.setText(str(sum(e.attempts for e in result.embryos)))
        ui.successLabel.setText(self._success_text(result.embryos))
        self._charts.redraw(force=True)

    def reset_display(self) -> None:
        ui = self.ui
        for label in (ui.toolStateLabel, ui.progressLabel, ui.attemptsLabel, ui.successLabel):
            label.setText("—")
        self._charts.reset()

    # -- formatting helpers --------------------------------------------------

    @staticmethod
    def _progress_text(embryos: list[Embryo]) -> str:
        moved = sum(1 for e in embryos if e.state == EmbryoState.MOVED)
        return f"{moved}/{len(embryos)}"

    @staticmethod
    def _success_text(embryos: list[Embryo]) -> str:
        moved = sum(1 for e in embryos if e.state == EmbryoState.MOVED)
        failed = sum(1 for e in embryos if e.state == EmbryoState.FAILED)
        if moved + failed == 0:
            return "—"
        return f"{100 * moved / (moved + failed):.0f}%"
