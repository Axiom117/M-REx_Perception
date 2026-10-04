"""Load and validate workspace YAML configs (``config/workspace/*.yaml``).

Defines the workspace schema (pydantic) and its loading entry point; generic
file-reading mechanics live in ``mrex_perception.config.loader``. Validation
mirrors ``src/setup/loadWorkspaceConfig.m``: all 11 fields are required and
``size`` / ``sourceregion`` / ``movedregion`` must hold 3 / 4 / 4 values.
YAML keys stay camelCase so the same files remain readable by the MATLAB
reference implementation. Python attribute names are snake_case (see
``mrex_perception.core.models.entities.Workspace``).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from mrex_perception.config.loader import config_root, load_config_mapping, require_fields
from mrex_perception.core.models import Workspace

REQUIRED_FIELDS = (
    "size",
    "sourceregion",
    "movedregion",
    "movedSpacing",
    "material",
    "surfaceHeight",
    "coeffFriction",
    "youngsModulus",
    "poissonRatio",
    "density",
    "surfaceEnergy",
)


class WorkspaceConfig(BaseModel):
    """Pydantic validation model for workspace YAML files."""

    model_config = ConfigDict(populate_by_name=True)

    size: list[float]
    source_region: list[float] = Field(alias="sourceregion")
    moved_region: list[float] = Field(alias="movedregion")
    moved_spacing: float = Field(alias="movedSpacing")
    material: str
    surface_height: float = Field(alias="surfaceHeight")
    coeff_friction: float = Field(alias="coeffFriction")
    youngs_modulus: float = Field(alias="youngsModulus")
    poisson_ratio: float = Field(alias="poissonRatio")
    density: float
    surface_energy: float = Field(alias="surfaceEnergy")

    @model_validator(mode="after")
    def _check_vector_lengths(self) -> WorkspaceConfig:
        if len(self.size) != 3 or len(self.source_region) != 4 or len(self.moved_region) != 4:
            raise ValueError(
                "size, sourceregion, and movedregion must contain 3, 4, and 4 values."
            )
        return self

    def to_workspace(self) -> Workspace:
        """Convert the validated config into the core ``Workspace`` model."""
        return Workspace(
            size=np.asarray(self.size, dtype=float),
            source_region=np.asarray(self.source_region, dtype=float),
            moved_region=np.asarray(self.moved_region, dtype=float),
            moved_spacing=self.moved_spacing,
            material=self.material,
            surface_height=self.surface_height,
            coeff_friction=self.coeff_friction,
            youngs_modulus=self.youngs_modulus,
            poisson_ratio=self.poisson_ratio,
            density=self.density,
            surface_energy=self.surface_energy,
        )


def workspace_config_dir() -> Path:
    """Repository ``config/workspace`` directory (external resource at packaging time)."""

    # return the path to the workspace config directory
    return config_root() / "workspace"


def load_workspace(config_name: str = "default", config_dir: Path | None = None) -> Workspace:
    """Load a workspace config by name (mirrors ``createWorkspace.m``)."""

    directory = Path(config_dir) if config_dir is not None else workspace_config_dir()
    data = load_config_mapping(config_name, directory, label="Workspace config")
    require_fields(data, REQUIRED_FIELDS, label="Workspace config")
    return WorkspaceConfig.model_validate(data).to_workspace()
