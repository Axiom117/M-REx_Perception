"""Live telemetry charts (pyqtgraph): tool Z, yaw and cumulative distance.

Samples accumulate from every engine snapshot, but the curves are only
redrawn every ``_REDRAW_SECONDS``: on macOS each Qt repaint competes with the
VTK swap chains, so per-frame chart redraws would throttle the whole UI.
"""

from __future__ import annotations

import time

import numpy as np
from pyqtgraph import PlotWidget

from mrex_perception.core.engine import Snapshot

_BACKGROUND = "#16181d"
_PENS = ("#4fc3f7", "#ffd400", "#22c55e")
_REDRAW_SECONDS = 0.5


class ChartRecorder:
    """Feeds the three dashboard plots from snapshots (accumulate + throttled redraw)."""

    def __init__(self, z_plot: PlotWidget, yaw_plot: PlotWidget, distance_plot: PlotWidget) -> None:
        plots = (z_plot, yaw_plot, distance_plot)
        titles = ("Z (mm)", "yaw (deg)", "distance (mm)")
        for plot, title in zip(plots, titles, strict=True):
            plot.setBackground(_BACKGROUND)
            plot.setTitle(title, color="#9aa4b2", size="9pt")
            plot.showGrid(x=True, y=True, alpha=0.15)
            plot.setMouseEnabled(x=False, y=False)
            plot.hideButtons()
            plot.setMenuEnabled(False)
        self._curves = [plot.plot(pen=pen) for plot, pen in zip(plots, _PENS, strict=True)]
        self.reset()

    def reset(self) -> None:
        self._steps: list[int] = []
        self._z: list[float] = []
        self._yaw: list[float] = []
        self._distance: list[float] = []
        self._total_distance = 0.0
        self._last_position: np.ndarray | None = None
        self._dirty = True
        self._last_redraw = 0.0
        self.redraw(force=True)

    def add(self, snapshot: Snapshot) -> None:
        """Accumulate one sample (no redraw); phase publishes are skipped."""
        step = snapshot.step_index
        if self._steps and step <= self._steps[-1]:
            return
        position = np.asarray(snapshot.tool.position, dtype=float)
        rotation = np.asarray(snapshot.tool.orientation, dtype=float)
        if self._last_position is not None:
            self._total_distance += float(np.linalg.norm(position - self._last_position))
        self._last_position = position

        self._steps.append(step)
        self._z.append(float(position[2]))
        self._yaw.append(float(np.degrees(np.arctan2(rotation[1, 0], rotation[0, 0]))))
        self._distance.append(self._total_distance)
        self._dirty = True

    def redraw(self, *, force: bool = False) -> None:
        """Repaint the curves, at most every ``_REDRAW_SECONDS`` unless forced."""
        if not self._dirty:
            return
        now = time.monotonic()
        if not force and now - self._last_redraw < _REDRAW_SECONDS:
            return
        self._last_redraw = now
        self._dirty = False
        self._curves[0].setData(self._steps, self._z)
        self._curves[1].setData(self._steps, self._yaw)
        self._curves[2].setData(self._steps, self._distance)
