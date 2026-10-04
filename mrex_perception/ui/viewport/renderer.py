"""Scene rendering for one viewport (v1: cached actors, matrix updates).

Actors are created once per embryo/tool and then only get their user matrix
(pose + scale) and color updated, so steady-state redraws are cheap. Overlays
(IDs / orientation arrows) are rebuilt only while their toggle is on.
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
from pyvista import Actor

from mrex_perception.core.engine import Snapshot
from mrex_perception.core.math import make_pose

EMBRYO_COLORS = {
    "free": "#ffffff",
    "selected": "#00e05a",
    "grasped": "#ffd400",
    "moved": "#3b82f6",
    "failed": "#ff4040",
    "clustered": "#e879f9",
}
TOOL_COLOR = "#ff2020"
ARROW_COLOR = "#f59e0b"
LABEL_COLOR = "#e8ecf2"

_BOX_COLOR = "#5b6472"
_GRID_COLOR = "#39404d"
_SOURCE_COLOR = "#3b82f6"
_MOVED_COLOR = "#22c55e"


class SceneRenderer:
    """Draws and updates the dynamic scene of a single plotter."""

    def __init__(self, plotter: pv.Plotter) -> None:
        self._plotter = plotter
        self._embryos: dict[int, Actor] = {}
        self._embryo_states: dict[int, str] = {}
        self._arrows: dict[int, Actor] = {}
        self._tool: Actor | None = None
        self._ids: Actor | None = None
        self._static: list[Actor] = []
        self._snapshot: Snapshot | None = None
        self.show_ids = False
        self.show_arrows = False

        self._embryo_mesh = pv.Sphere(radius=1.0, theta_resolution=20, phi_resolution=14)
        self._tool_mesh = pv.Cylinder(radius=0.5, height=1.0, direction=(0.0, 0.0, 1.0))
        self._arrow_mesh = pv.Arrow(start=(0.0, 0.0, 0.0), direction=(1.0, 0.0, 0.0), scale=1.0)

    # -- static scene --------------------------------------------------------

    def set_workspace(
        self,
        size: np.ndarray | tuple[float, float, float],
        source_region: np.ndarray | None = None,
        moved_region: np.ndarray | None = None,
    ) -> None:
        """Draw the bounding box, ground grid and (optionally) both region rectangles."""
        for actor in self._static:
            self._plotter.remove_actor(actor)
        self._static.clear()

        width, height, depth = (float(v) for v in size)
        self._static.append(
            self._plotter.add_mesh(
                pv.Box(bounds=(0, width, 0, height, 0, depth)),
                style="wireframe",
                color=_BOX_COLOR,
                line_width=1,
                reset_camera=False,
            )
        )
        ground = pv.Plane(
            center=(width / 2, height / 2, 0),
            direction=(0, 0, 1),
            i_size=width,
            j_size=height,
            i_resolution=10,
            j_resolution=4,
        )
        self._static.append(
            self._plotter.add_mesh(
                ground, style="wireframe", color=_GRID_COLOR, line_width=1, reset_camera=False
            )
        )
        for region, color in ((source_region, _SOURCE_COLOR), (moved_region, _MOVED_COLOR)):
            if region is None:
                continue
            x, y, w, h = (float(v) for v in region)
            rect = pv.Plane(
                center=(x + w / 2, y + h / 2, 0.05), direction=(0, 0, 1), i_size=w, j_size=h
            )
            self._static.append(
                self._plotter.add_mesh(
                    rect, color=color, opacity=0.15, reset_camera=False, lighting=False
                )
            )
        self._plotter.render()

    # -- dynamic scene -------------------------------------------------------

    def update(self, snapshot: Snapshot) -> None:
        """Apply a snapshot to the cached actors (matrices, colors, overlays)."""
        self._snapshot = snapshot
        self._sync_embryos(snapshot)
        self._update_tool(snapshot)
        self._update_overlays(snapshot)
        self._plotter.render()

    def clear(self) -> None:
        """Remove all run objects (embryos, tool, overlays) and forget the snapshot."""
        for actor in (*self._embryos.values(), *self._arrows.values(), self._ids, self._tool):
            if actor is not None:
                self._plotter.remove_actor(actor)
        self._embryos.clear()
        self._embryo_states.clear()
        self._arrows.clear()
        self._ids = None
        self._tool = None
        self._snapshot = None
        self._plotter.render()

    def set_show_ids(self, show: bool) -> None:
        self.show_ids = show
        if self._snapshot is not None:
            self._update_overlays(self._snapshot)
            self._plotter.render()

    def set_show_arrows(self, show: bool) -> None:
        self.show_arrows = show
        if self._snapshot is not None:
            self._update_overlays(self._snapshot)
            self._plotter.render()

    # -- internals -----------------------------------------------------------

    def _sync_embryos(self, snapshot: Snapshot) -> None:
        current = {embryo.id for embryo in snapshot.embryos}
        for embryo_id in [i for i in self._embryos if i not in current]:
            self._plotter.remove_actor(self._embryos.pop(embryo_id))
            self._embryo_states.pop(embryo_id, None)

        for embryo in snapshot.embryos:
            actor = self._embryos.get(embryo.id)
            if actor is None:
                actor = self._plotter.add_mesh(
                    self._embryo_mesh,
                    color=EMBRYO_COLORS["free"],
                    smooth_shading=True,
                    reset_camera=False,
                )
                self._embryos[embryo.id] = actor
            actor.user_matrix = make_pose(embryo.orientation, embryo.position) @ np.diag(
                [embryo.length / 2, embryo.width / 2, embryo.height / 2, 1.0]
            )
            state = str(embryo.state)
            if self._embryo_states.get(embryo.id) != state:
                actor.prop.color = EMBRYO_COLORS.get(state, EMBRYO_COLORS["free"])
                self._embryo_states[embryo.id] = state

    def _update_tool(self, snapshot: Snapshot) -> None:
        tool = snapshot.tool
        if self._tool is None:
            self._tool = self._plotter.add_mesh(
                self._tool_mesh, color=TOOL_COLOR, smooth_shading=True, reset_camera=False
            )
        self._tool.user_matrix = make_pose(tool.orientation, tool.position) @ np.diag(
            [2 * tool.radius, 2 * tool.radius, tool.height, 1.0]
        )

    def _update_overlays(self, snapshot: Snapshot) -> None:
        # IDs: one label actor rebuilt in place while enabled.
        if self._ids is not None:
            self._plotter.remove_actor(self._ids)
            self._ids = None
        if self.show_ids and snapshot.embryos:
            points = [
                embryo.position + np.array([0.0, 0.0, embryo.height / 2 + 0.3])
                for embryo in snapshot.embryos
            ]
            self._ids = self._plotter.add_point_labels(
                points,
                [str(embryo.id) for embryo in snapshot.embryos],
                name="embryo_ids",
                show_points=False,
                shape=None,
                fill_shape=False,
                font_size=10,
                text_color=LABEL_COLOR,
                always_visible=True,
                reset_camera=False,
            )

        # Arrows: cached actor per embryo, direction = orientation @ +X, length = embryo length.
        current = {embryo.id for embryo in snapshot.embryos}
        for embryo_id in [i for i in self._arrows if i not in current]:
            self._plotter.remove_actor(self._arrows.pop(embryo_id))
        if not self.show_arrows:
            for arrow_actor in self._arrows.values():
                self._plotter.remove_actor(arrow_actor)
            self._arrows.clear()
            return
        for embryo in snapshot.embryos:
            actor = self._arrows.get(embryo.id)
            if actor is None:
                actor = self._plotter.add_mesh(
                    self._arrow_mesh, color=ARROW_COLOR, line_width=2, reset_camera=False
                )
                self._arrows[embryo.id] = actor
            length = embryo.length
            actor.user_matrix = make_pose(embryo.orientation, embryo.position) @ np.diag(
                [length, length, length, 1.0]
            )
