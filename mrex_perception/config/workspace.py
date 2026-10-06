"""Load and validate workspace YAML configs (``config/workspace/*.yaml``).

Defines the workspace schema (pydantic) and its loading entry point; generic
file-reading mechanics live in ``mrex_perception.config.loader``. YAML keys
are snake_case and match the Python attribute names; required fields are
enforced natively by pydantic (a missing key raises ``ValidationError``), and
``size`` / ``source_region`` / ``moved_region`` must hold 3 / 4 / 4 values.
The validated config is converted into the core ``Workspace`` model (see
``mrex_perception.core.models.entities.Workspace``).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from pydantic import BaseModel, model_validator

from mrex_perception.config.loader import config_root, load_config_mapping
from mrex_perception.core.models import Workspace


class WorkspaceConfig(BaseModel):
    """Pydantic validation model for workspace YAML files (snake_case keys)."""

    size: list[float]
    source_region: list[float]
    moved_region: list[float]
    moved_spacing: float
    material: str
    surface_height: float
    coeff_friction: float
    youngs_modulus: float
    poisson_ratio: float
    density: float
    surface_energy: float

    @model_validator(mode="after")
    def _check_vector_lengths(self) -> WorkspaceConfig:
        if len(self.size) != 3 or len(self.source_region) != 4 or len(self.moved_region) != 4:
            raise ValueError(
                "size, source_region, and moved_region must contain 3, 4, and 4 values."
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
    """Load a workspace config by name (required fields are enforced by pydantic)."""

    directory = Path(config_dir) if config_dir is not None else workspace_config_dir()
    data = load_config_mapping(config_name, directory, label="Workspace config")
    return WorkspaceConfig.model_validate(data).to_workspace()


def list_workspace_configs(config_dir: Path | None = None) -> list[str]:
    """Names of the available workspace configs (``*.yaml`` / ``*.yml`` stems).

    Sorted and de-duplicated; an empty list means no configs were found
    (e.g. the directory does not exist).
    """

    directory = Path(config_dir) if config_dir is not None else workspace_config_dir()
    stems = {path.stem for pattern in ("*.yaml", "*.yml") for path in directory.glob(pattern)}
    return sorted(stems)
