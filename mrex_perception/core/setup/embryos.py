"""Embryo placement and clustering.

Ports of ``src/setup/populateEmbryos.m``, ``src/setup/createEmbryoFromYOLO.m``
and ``src/detection/detectClusteredEmbryos.m``.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from mrex_perception.core.math import pixel_to_workspace, rotation_z
from mrex_perception.core.models import Embryo, EmbryoSpec, EmbryoState, Workspace


def populate_random(
    count: int,
    workspace: Workspace,
    rng: np.random.Generator,
    spec: EmbryoSpec | None = None,
) -> list[Embryo]:
    """Randomly place ``count`` embryos in the source region.

    Best-effort rejection sampling (port of ``populateEmbryos.m``): up to 1000
    candidate attempts per embryo, distances are full 3D distances, and the
    last candidate is accepted if no spot was free. z is fixed at 0.1 mm and
    yaw is drawn uniformly from [0, 2*pi). Geometry and the minimum spacing
    come from ``spec`` (defaults mirror ``config/embryo/default.yaml``);
    randomness comes from the injected ``rng`` so results are reproducible
    for a fixed seed.
    """
    spec = EmbryoSpec() if spec is None else spec
    source_x, source_y, source_w, source_h = workspace.source_region

    embryos: list[Embryo] = []
    for i in range(count):
        position: np.ndarray | None = None
        candidate = np.zeros(3)
        for _ in range(1000):
            candidate = np.array(
                [source_x + rng.random() * source_w, source_y + rng.random() * source_h, 0.1]
            )
            if all(np.linalg.norm(e.position - candidate) >= spec.min_spacing for e in embryos):
                position = candidate
                break
        if position is None:
            position = candidate  # best effort, aligned with MATLAB
        yaw = 2 * np.pi * rng.random()
        embryos.append(
            Embryo(
                id=i + 1,
                shape=spec.shape,
                width=spec.width,
                length=spec.length,
                height=spec.height,
                position=position,
                orientation=rotation_z(yaw),
            )
        )
    return embryos


def from_detections(
    records: Sequence[Mapping[str, Any]],
    workspace: Workspace,
    spec: EmbryoSpec | None = None,
) -> list[Embryo]:
    """Build embryos from YOLO detection records.

    Records follow the CSV contract from the architecture doc (§10.2):
    ``image, image_width, image_height, class_id, confidence, x, y, width,
    height, theta``. Port of ``createEmbryoFromYOLO.m``: confidence filter
    ``>= spec.min_confidence``, ``yaw = -theta``, pixel positions mapped via
    ``pixel_to_workspace`` using the image size of the first record; geometry
    comes from ``spec``.
    """
    spec = EmbryoSpec() if spec is None else spec
    detections = [
        record for record in records if float(record["confidence"]) >= spec.min_confidence
    ]
    if not detections:
        warnings.warn("No embryos detected", stacklevel=2)
        return []

    image_width = float(detections[0]["image_width"])
    image_height = float(detections[0]["image_height"])

    embryos: list[Embryo] = []
    for i, record in enumerate(detections):
        position = pixel_to_workspace(
            float(record["x"]), float(record["y"]), image_width, image_height, workspace
        )
        yaw = -float(record["theta"])
        embryos.append(
            Embryo(
                id=i + 1,
                shape=spec.shape,
                width=spec.width,
                length=spec.length,
                height=spec.height,
                confidence=float(record["confidence"]),
                position=position,
                orientation=rotation_z(yaw),
            )
        )
    return embryos


def mark_clustered(embryos: list[Embryo], threshold: float = 1.0) -> list[Embryo]:
    """Flag embryos closer than ``threshold`` as clustered (in place).

    ``threshold`` is ``EmbryoSpec.cluster_threshold`` (the engine passes the
    configured value through). Port of ``detectClusteredEmbryos.m``: distances
    use only the xy plane;
    both members of a close pair get ``is_clustered=True`` and their state is
    overwritten to ``clustered`` unconditionally (MATLAB behavior, see doc
    §16-①). The flag is reset for every embryo first, but ``state`` is not.
    Returns ``embryos`` unchanged so ``embryos = mark_clustered(embryos)``
    works as in the MATLAB reference.
    """
    for embryo in embryos:
        embryo.is_clustered = False
    for i, embryo_i in enumerate(embryos):
        for embryo_j in embryos[i + 1 :]:
            distance = np.linalg.norm(embryo_i.position[:2] - embryo_j.position[:2])
            if distance < threshold:
                embryo_i.is_clustered = True
                embryo_j.is_clustered = True
                embryo_i.state = EmbryoState.CLUSTERED
                embryo_j.state = EmbryoState.CLUSTERED
    return embryos
