"""Planning helpers (ports of ``src/planning/*.m``).

Selection follows MATLAB exactly: only ``free`` embryos can be selected,
``clustered`` ones never participate (migration plan §16-①). Embryo "IDs" are
1-based and follow the list position convention (``embryos[id - 1]``).
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import ArrayLike

from mrex_perception.core.models import Embryo, Workspace
from mrex_perception.core.states import EmbryoState


def has_free_embryos(embryos: list[Embryo]) -> bool:
    """True while at least one embryo is in state ``free`` (``hasFreeEmbryos.m``)."""
    return any(e.state == EmbryoState.FREE for e in embryos)


def select_nearest_free(embryos: list[Embryo], target_point: ArrayLike) -> list[Embryo]:
    """Select the free embryo nearest to ``target_point`` (``selectNearEmbryo.m``).

    Full 3D distance, strict ``<`` so ties keep the earliest embryo. Warns and
    leaves ``embryos`` untouched when no free embryo is left.
    """
    target = np.asarray(target_point, dtype=float)
    best_distance = np.inf
    target_index = -1
    for i, embryo in enumerate(embryos):
        if embryo.state == EmbryoState.FREE:
            distance = float(np.linalg.norm(embryo.position - target))
            if distance < best_distance:
                best_distance = distance
                target_index = i

    if target_index < 0:
        warnings.warn("No embryos left to select", stacklevel=2)
        return embryos
    return select_embryo(embryos, target_index + 1)


def select_embryo(embryos: list[Embryo], target_id: int) -> list[Embryo]:
    """Select ``embryos[target_id - 1]`` after freeing any previous selection.

    Port of ``selectEmbryos.m``: every ``selected`` embryo is reset to ``free``
    first, then the target is set to ``selected`` (clear-then-set).
    """
    for embryo in embryos:
        if embryo.state == EmbryoState.SELECTED:
            embryo.state = EmbryoState.FREE
    embryos[target_id - 1].state = EmbryoState.SELECTED
    return embryos


def next_moved_position(embryos: list[Embryo], workspace: Workspace) -> np.ndarray:
    """Next grid slot in the moved region (port of ``getMovedPosition.m``).

    ``spacing = embryos[0].length * workspace.moved_spacing``,
    ``num_cols = floor(region_width / spacing)``, ``col = moved_count % num_cols``,
    ``row = moved_count // num_cols``; z is ``embryos[0].height / 2``. Raises
    ``ValueError`` when the region is full (same messages as MATLAB).
    """
    moved_count = sum(1 for e in embryos if e.state == EmbryoState.MOVED)

    x_start, y_start, region_width, region_height = workspace.moved_region
    spacing = float(embryos[0].length) * float(workspace.moved_spacing)
    num_cols = int(np.floor(region_width / spacing)) if spacing > 0 else 0

    if num_cols < 1:
        # MATLAB quirk: mod(x, 0) returns x and floor(x / 0) is Inf/NaN there,
        # so for moved_count > 0 the height-overflow branch fires first while
        # the explicit `num_cols < 1` check is what surfaces for moved_count 0.
        if moved_count > 0:
            raise ValueError(
                "Moved region is full. Use fewer embryo or increase size of the region"
            )
        raise ValueError("Region is full")

    col = moved_count % num_cols
    row = moved_count // num_cols
    x = x_start + spacing / 2 + col * spacing
    y = y_start + spacing / 2 + row * spacing
    z = embryos[0].height / 2
    moved_position = np.array([x, y, z])

    # capacity limit (checked after computing the slot, as in MATLAB)
    if y + spacing / 2 > y_start + region_height:
        raise ValueError("Moved region is full. Use fewer embryo or increase size of the region")

    return moved_position
