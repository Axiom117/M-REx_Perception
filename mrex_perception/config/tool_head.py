"""Load and validate tool head YAML configs (``config/tool_head/*.yaml``).

Defines the tool head schema (pydantic): body geometry, the interaction
surface (droplet contact patch), the adhesion/pickup model coefficients and
the kinematics values. YAML keys are snake_case; all fields are required
(pydantic) and ``home_offset`` must hold 3 values. ``to_tool_head()`` builds a
fresh core ``ToolHead`` for a run -- the tool head is stateful, so the config
holds the validated values and the caller materialises one instance per run
(see ``mrex_perception.config.app.AppConfig.tool``).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from mrex_perception.config.loader import config_root, load_config_mapping
from mrex_perception.core.models import ToolHead, Workspace


class ContactSurfaceConfig(BaseModel):
    """Interaction surface (droplet contact patch) geometry."""

    shape: str
    radius: float = Field(gt=0)


class AdhesionConfig(BaseModel):
    """Adhesion / pickup model coefficients (see ``pickup_probability``)."""

    model: str
    base_probability: float
    reference_width: float = Field(gt=0)
    attempt_penalty: float
    max_attempts: int = Field(ge=1)


class ToolHeadConfig(BaseModel):
    """Pydantic validation model for tool head YAML files (snake_case keys)."""

    name: str
    shape: str
    diameter: float = Field(gt=0)
    height: float = Field(gt=0)
    contact_surface: ContactSurfaceConfig
    adhesion: AdhesionConfig
    clearance: float
    max_velocity: float
    home_offset: list[float]

    @model_validator(mode="after")
    def _check_home_offset(self) -> ToolHeadConfig:
        if len(self.home_offset) != 3:
            raise ValueError("home_offset must contain 3 values.")
        return self

    def to_tool_head(self, workspace: Workspace) -> ToolHead:
        """Build a fresh core ``ToolHead`` (home position from ``home_offset``).

        The nested groups flatten onto the core model: ``contact_surface`` ->
        ``contact_shape`` / ``contact_radius``; ``adhesion.model`` ->
        ``adhesion_model`` and the remaining coefficients keep their names.
        """
        dx, dy, dz = self.home_offset
        tool = ToolHead.for_workspace(workspace, home_offset=(dx, dy, dz))
        tool.name = self.name
        tool.shape = self.shape
        tool.diameter = self.diameter
        tool.height = self.height
        tool.contact_shape = self.contact_surface.shape
        tool.contact_radius = self.contact_surface.radius
        tool.clearance = self.clearance
        tool.max_velocity = self.max_velocity
        tool.adhesion_model = self.adhesion.model
        tool.base_probability = self.adhesion.base_probability
        tool.reference_width = self.adhesion.reference_width
        tool.attempt_penalty = self.adhesion.attempt_penalty
        tool.max_attempts = self.adhesion.max_attempts
        return tool


def tool_head_config_dir() -> Path:
    """Repository ``config/tool_head`` directory (external resource at packaging time)."""
    return config_root() / "tool_head"


def load_tool_head(config_name: str = "default", config_dir: Path | None = None) -> ToolHeadConfig:
    """Load a tool head config by name (required fields are enforced by pydantic)."""
    directory = Path(config_dir) if config_dir is not None else tool_head_config_dir()
    data = load_config_mapping(config_name, directory, label="Tool head config")
    return ToolHeadConfig.model_validate(data)


def list_tool_head_configs(config_dir: Path | None = None) -> list[str]:
    """Names of the available tool head configs (``*.yaml`` stems, sorted)."""
    directory = Path(config_dir) if config_dir is not None else tool_head_config_dir()
    return sorted(path.stem for path in directory.glob("*.yaml"))
