from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from mrex_perception.core.math import make_pose

from .states import EmbryoState, ToolState


# Data classes for core domain models, eq disabled to avoid ambiguity with numpy array comparisons.
@dataclass(eq=False)
class Workspace:
    """Workspace configuration (see ``config/workspace/default.yaml``)."""

    size: np.ndarray  # (3,) extents x, y, z in mm
    source_region: np.ndarray  # (4,) [x, y, w, h] in mm
    moved_region: np.ndarray  # (4,) [x, y, w, h] in mm
    moved_spacing: float  # placement spacing factor (x embryo length)
    material: str
    surface_height: float
    coeff_friction: float
    youngs_modulus: float
    poisson_ratio: float
    density: float
    surface_energy: float


@dataclass(eq=False)
class Embryo:
    """Single embryo (fields align with the MATLAB embryo structs)."""

    id: int  # 1-based (MATLAB semantics)
    state: EmbryoState = EmbryoState.FREE
    attempts: int = 0
    picked_successfully: bool = False
    shape: str = "ellipsoid"
    width: float = 0.2
    length: float = 0.5
    height: float = 0.2
    confidence: float = 1.0
    position: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 0.1]))
    orientation: np.ndarray = field(default_factory=lambda: np.eye(3))
    is_clustered: bool = False

    @property
    def pose(self) -> np.ndarray:
        """4x4 pose assembled from orientation and position."""
        return make_pose(self.orientation, self.position)


@dataclass(eq=False)
class EmbryoSpec:
    """Embryo batch template: creation geometry + setup thresholds.

    Embryos are per-instance objects, so the config layer hands over this
    template (``config/embryo/*.yaml``); setup functions read geometry and
    thresholds from it while instance state stays on ``Embryo``.
    """

    shape: str = "ellipsoid"
    width: float = 0.2
    length: float = 0.5
    height: float = 0.2
    min_confidence: float = 0.8
    cluster_threshold: float = 1.0
    min_spacing: float = 1.0


@dataclass(eq=False)
class ToolHead:
    """Adhesion tool head (fields align with ``createToolHead.m``).

    Interaction-surface geometry, adhesion/pickup coefficients and the grasp
    policy are config-driven (``config/tool_head/*.yaml``); the dataclass
    defaults mirror ``config/tool_head/default.yaml``.
    """

    name: str = "adhesionTool"
    contact_radius: float = 0.25
    contact_shape: str = "circular"
    diameter: float = 1.5
    height: float = 0.5
    clearance: float = 1.0
    shape: str = "cylinder"
    state: ToolState = ToolState.HOME
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    orientation: np.ndarray = field(default_factory=lambda: np.eye(3))
    has_embryo: bool = False
    attached_embryo_id: int = 0
    adhesion_model: str = "vanDerWaalsDroplet"
    base_probability: float = 0.7
    reference_width: float = 0.2
    attempt_penalty: float = 0.05
    max_attempts: int = 3
    home_position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    target_position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: float = 0.0
    max_velocity: float = 10.0
    path: list[np.ndarray] = field(default_factory=list)

    @classmethod
    def for_workspace(
        cls,
        workspace: Workspace,
        *,
        home_offset: tuple[float, float, float] = (15.0, 15.0, 10.0),
    ) -> ToolHead:
        """Build the tool head (default values) with its initial (home) position.

        The initial position is ``[source_x / 2 + dx, source_y / 2 + dy, dz]``
        with ``home_offset = (dx, dy, dz)`` -> ``[15, 17.5, 10]`` for the
        default config (port of ``src/setup/createToolHead.m``; x/y halve the
        source-region origin, not its center). Home and target position start
        at the same point.
        """
        dx, dy, dz = home_offset
        position = np.array(
            [
                workspace.source_region[0] / 2 + dx,
                workspace.source_region[1] / 2 + dy,
                dz,
            ]
        )
        tool = cls(position=position)
        tool.home_position = position.copy()
        tool.target_position = position.copy()
        return tool

    @property
    def radius(self) -> float:
        """Cylinder radius (= diameter / 2, as in createToolHead.m)."""
        return self.diameter / 2

    @property
    def pose(self) -> np.ndarray:
        """4x4 pose assembled from orientation and position."""
        return make_pose(self.orientation, self.position)
