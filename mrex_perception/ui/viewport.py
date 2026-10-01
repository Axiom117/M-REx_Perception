"""Multi-viewport 3D panel (Top / Front / Right) built on PyVista's QtInteractor.

M0 scope: three orthographic CAD-style views (Rhino-like) with a placeholder
scene (workspace bounding box + ground grid). The workspace size will come from
the YAML config loader in M1; the embryo/tool meshes arrive in M4.
"""

from __future__ import annotations

import pyvista as pv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

# Placeholder workspace size (mm); replaced by the config loader in M1.
PLACEHOLDER_WORKSPACE_SIZE = (100.0, 40.0, 10.0)

_BACKGROUND = "#16181d"
_BOX_COLOR = "#5b6472"
_GRID_COLOR = "#39404d"


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

        grid = QGridLayout(self)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(4)

        grid.addWidget(self._titled("Top (XY)", self.top), 0, 0)
        grid.addWidget(self._titled("Front (XZ)", self.front), 0, 1)
        grid.addWidget(self._titled("Right (YZ)", self.right), 1, 0)

        placeholder = QLabel("预留：透视图 / 遥测（M4）")
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
        self.set_workspace_box(PLACEHOLDER_WORKSPACE_SIZE)

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

    def set_workspace_box(self, size: tuple[float, float, float]) -> None:
        """Draw the workspace bounding box and ground grid in every viewport."""
        width, height, depth = size
        for view in self._views.values():
            view.add_mesh(
                pv.Box(bounds=(0, width, 0, height, 0, depth)),
                style="wireframe",
                color=_BOX_COLOR,
                line_width=1,
            )
            ground = pv.Plane(
                center=(width / 2, height / 2, 0),
                direction=(0, 0, 1),
                i_size=width,
                j_size=height,
                i_resolution=10,
                j_resolution=4,
            )
            view.add_mesh(ground, style="wireframe", color=_GRID_COLOR, line_width=1)
        self.fit_all()

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
