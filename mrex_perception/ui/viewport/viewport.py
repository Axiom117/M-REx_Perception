"""Multi-viewport 3D panel (Top / Front / Right) built on PyVista's QtInteractor.

Three orthographic CAD-style views (Rhino-like) sharing one scene renderer set.
The static scene comes from the workspace config; dynamic objects are updated
from engine snapshots, always on the UI thread.
"""

from __future__ import annotations

from typing import cast

import pyvista as pv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from mrex_perception.core.engine import Snapshot
from mrex_perception.core.models import Workspace

from .renderer import SceneRenderer

_BACKGROUND = "#16181d"
_PREVIEW_SIZE = (100.0, 40.0, 10.0)  # shown until MainWindow supplies the config


class MultiViewPanel(QWidget):
    """2x2 grid with three independent orthographic viewports."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.top = QtInteractor(self)
        self.front = QtInteractor(self)
        self.right = QtInteractor(self)

        self._views: dict[str, QtInteractor] = {
            "top": self.top,
            "front": self.front,
            "right": self.right,
        }
        self._renderers = {
            name: SceneRenderer(cast(pv.Plotter, view)) for name, view in self._views.items()
        }

        grid = QGridLayout(self)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(4)

        grid.addWidget(self._titled("Top (XY)", self.top), 0, 0)
        grid.addWidget(self._titled("Front (XZ)", self.front), 0, 1)
        grid.addWidget(self._titled("Right (YZ)", self.right), 1, 0)

        placeholder = QLabel("预留：运行汇总 / 日志（后续）")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(
            "color: #5b6472; border: 1px dashed #3a3f4b; border-radius: 6px;"
        )
        grid.addWidget(placeholder, 1, 1)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self._configure_views()
        for renderer in self._renderers.values():
            renderer.set_workspace(_PREVIEW_SIZE)
        self.fit_all()

    # -- public API ----------------------------------------------------------

    def fit_all(self) -> None:
        """Fit the camera to the scene in every viewport (keeps orientation)."""
        for view in self._views.values():
            view.reset_camera()

    def reset_views(self) -> None:
        """Restore the default orientation presets and refit every viewport."""
        for name, view in self._views.items():
            self._apply_orientation(view, name)
        self.fit_all()

    def set_workspace(self, workspace: Workspace) -> None:
        """Draw the workspace box, ground grid and region rectangles from the config."""
        for renderer in self._renderers.values():
            renderer.set_workspace(workspace.size, workspace.source_region, workspace.moved_region)
        # Frame the workspace box (MATLAB xlim/ylim/zlim), not the 180 mm moved region quirk.
        width, height, depth = (float(v) for v in workspace.size)
        for view in self._views.values():
            view.reset_camera(bounds=(0.0, width, 0.0, height, 0.0, depth))

    def update_scene(self, snapshot: Snapshot) -> None:
        """Apply one engine snapshot to all views."""
        for renderer in self._renderers.values():
            renderer.update(snapshot)

    def clear_scene(self) -> None:
        """Remove all run objects from every view (Reset)."""
        for renderer in self._renderers.values():
            renderer.clear()

    def set_show_ids(self, show: bool) -> None:
        for renderer in self._renderers.values():
            renderer.set_show_ids(show)

    def set_show_arrows(self, show: bool) -> None:
        for renderer in self._renderers.values():
            renderer.set_show_arrows(show)

    def close_plotters(self) -> None:
        """Close every VTK interactor (must run on the UI thread before quitting)."""
        for view in self._views.values():
            view.close()

    # -- setup helpers -------------------------------------------------------

    def _configure_views(self) -> None:
        for name, view in self._views.items():
            view.set_background(_BACKGROUND)
            view.add_axes()
            view.enable_parallel_projection()
            self._apply_orientation(view, name)

    @staticmethod
    def _apply_orientation(view: QtInteractor, orientation: str) -> None:
        if orientation == "top":
            view.view_xy()
        elif orientation == "front":
            view.view_xz()
        else:
            view.view_yz()

    @staticmethod
    def _titled(title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label = QLabel(title)
        label.setStyleSheet("color: #9aa4b2; padding-left: 4px;")
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return container
