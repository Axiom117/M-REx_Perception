"""Load and validate embryo YAML configs (``config/embryo/*.yaml``).

Defines the embryo schema (pydantic): the batch geometry used when embryos
are created (random placement / YOLO detections) plus the detection,
clustering and placement thresholds. YAML keys are snake_case; all fields are
required (pydantic). ``to_embryo_spec()`` flattens the groups into the core
``EmbryoSpec`` template consumed by the setup functions.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from mrex_perception.config.loader import config_root, load_config_mapping
from mrex_perception.core.models import EmbryoSpec


class DetectionConfig(BaseModel):
    """Detection acceptance filter (``from_detections``)."""

    min_confidence: float = Field(ge=0, le=1)


class ClusteringConfig(BaseModel):
    """Clustering threshold (``mark_clustered``, xy distance in mm)."""

    threshold: float = Field(gt=0)


class PlacementConfig(BaseModel):
    """Random placement minimum spacing (``populate_random``)."""

    min_spacing: float = Field(ge=0)


class EmbryoConfig(BaseModel):
    """Pydantic validation model for embryo YAML files (snake_case keys)."""

    shape: str
    width: float = Field(gt=0)
    length: float = Field(gt=0)
    height: float = Field(gt=0)
    detection: DetectionConfig
    clustering: ClusteringConfig
    placement: PlacementConfig

    def to_embryo_spec(self) -> EmbryoSpec:
        """Flatten the validated config into the core ``EmbryoSpec`` template."""
        return EmbryoSpec(
            shape=self.shape,
            width=self.width,
            length=self.length,
            height=self.height,
            min_confidence=self.detection.min_confidence,
            cluster_threshold=self.clustering.threshold,
            min_spacing=self.placement.min_spacing,
        )


def embryo_config_dir() -> Path:
    """Repository ``config/embryo`` directory (external resource at packaging time)."""
    return config_root() / "embryo"


def load_embryo(config_name: str = "default", config_dir: Path | None = None) -> EmbryoSpec:
    """Load an embryo config by name and convert it into the core ``EmbryoSpec``."""
    directory = Path(config_dir) if config_dir is not None else embryo_config_dir()
    data = load_config_mapping(config_name, directory, label="Embryo config")
    return EmbryoConfig.model_validate(data).to_embryo_spec()


def list_embryo_configs(config_dir: Path | None = None) -> list[str]:
    """Names of the available embryo configs (``*.yaml`` stems, sorted)."""
    directory = Path(config_dir) if config_dir is not None else embryo_config_dir()
    return sorted(path.stem for path in directory.glob("*.yaml"))
