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
class ToolHead:
    """Adhesion tool head (fields align with ``createToolHead.m``)."""

    name: str = "adhesionTool"
    contact_radius: float = 0.25
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
    home_position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    target_position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: float = 0.0
    max_velocity: float = 10.0
    path: list[np.ndarray] = field(default_factory=list)

    @property
    def radius(self) -> float:
        """Cylinder radius (= diameter / 2, as in createToolHead.m)."""
        return self.diameter / 2

    @property
    def pose(self) -> np.ndarray:
        """4x4 pose assembled from orientation and position."""
        return make_pose(self.orientation, self.position)
