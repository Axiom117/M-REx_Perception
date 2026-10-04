"""Planner helpers: free check, nearest selection, moved grid (M2)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.models import Embryo, EmbryoState
from mrex_perception.core.sim import (
    has_free_embryos,
    next_moved_position,
    select_embryo,
    select_nearest_free,
)

TARGET = np.array([50.0, 50.0, 0.1])


def _embryo(
    i: int,
    state: EmbryoState = EmbryoState.FREE,
    position: tuple[float, float, float] = (0.0, 0.0, 0.1),
) -> Embryo:
    return Embryo(id=i, state=state, position=np.array(position, dtype=float))


def _moved_scenario(count: int) -> list[Embryo]:
    """Default-sized embryos, the first ``count`` of them moved (>= 6 embryos)."""
    size = max(count, 6)
    return [
        _embryo(i + 1, EmbryoState.MOVED if i < count else EmbryoState.FREE)
        for i in range(size)
    ]


# -- has_free_embryos --------------------------------------------------------


def test_has_free_embryos() -> None:
    assert has_free_embryos([_embryo(1), _embryo(2, EmbryoState.CLUSTERED)])
    assert not has_free_embryos(
        [_embryo(1, EmbryoState.CLUSTERED), _embryo(2, EmbryoState.MOVED)]
    )
    assert not has_free_embryos([])


# -- select_nearest_free -----------------------------------------------------


def test_select_nearest_free_skips_non_free() -> None:
    near_but_clustered = _embryo(1, EmbryoState.CLUSTERED, (49.0, 50.0, 0.1))
    nearest = _embryo(2, EmbryoState.FREE, (40.0, 50.0, 0.1))
    farther = _embryo(3, EmbryoState.FREE, (10.0, 10.0, 0.1))
    embryos = [near_but_clustered, nearest, farther]

    result = select_nearest_free(embryos, TARGET)

    assert result is embryos
    assert nearest.state == EmbryoState.SELECTED
    assert farther.state == EmbryoState.FREE
    assert near_but_clustered.state == EmbryoState.CLUSTERED


def test_select_nearest_free_resets_previous_selection() -> None:
    previous = _embryo(1, EmbryoState.SELECTED, (40.0, 50.0, 0.1))
    nearest = _embryo(2, EmbryoState.FREE, (10.0, 10.0, 0.1))

    select_nearest_free([previous, nearest], np.array([0.0, 0.0, 0.0]))

    assert previous.state == EmbryoState.FREE
    assert nearest.state == EmbryoState.SELECTED


def test_select_nearest_free_warns_when_none_left() -> None:
    embryos = [_embryo(1, EmbryoState.CLUSTERED), _embryo(2, EmbryoState.MOVED)]
    with pytest.warns(UserWarning, match="No embryos left to select"):
        result = select_nearest_free(embryos, TARGET)
    assert result is embryos
    assert [e.state for e in embryos] == [EmbryoState.CLUSTERED, EmbryoState.MOVED]


# -- select_embryo -----------------------------------------------------------


def test_select_embryo_is_one_based_and_resets_others() -> None:
    embryos = [_embryo(1, EmbryoState.SELECTED), _embryo(2), _embryo(3)]

    select_embryo(embryos, 3)

    assert [e.state for e in embryos] == [
        EmbryoState.FREE,
        EmbryoState.FREE,
        EmbryoState.SELECTED,
    ]


# -- next_moved_position -----------------------------------------------------


def test_next_moved_position_grid() -> None:
    ws = load_workspace("default")  # spacing = 0.5 * 4 = 2; num_cols = floor(100 / 2) = 50

    assert next_moved_position(_moved_scenario(0), ws) == pytest.approx([81.0, 6.0, 0.1])
    assert next_moved_position(_moved_scenario(1), ws) == pytest.approx([83.0, 6.0, 0.1])
    assert next_moved_position(_moved_scenario(49), ws) == pytest.approx([179.0, 6.0, 0.1])
    assert next_moved_position(_moved_scenario(50), ws) == pytest.approx([81.0, 8.0, 0.1])


def test_next_moved_position_uses_first_embryo_dimensions() -> None:
    ws = load_workspace("default")
    embryos = _moved_scenario(0)
    embryos[0].length = 0.25  # spacing = 1.0 -> col step 1.0
    embryos[0].height = 0.4

    position = next_moved_position(embryos, ws)

    assert position == pytest.approx([80.5, 5.5, 0.2])


def test_next_moved_position_region_full_error() -> None:
    ws = load_workspace("default")
    ws.moved_region = np.array([80.0, 5.0, 4.0, 3.0])  # spacing 2 -> num_cols 2, height 3

    with pytest.raises(ValueError, match="Moved region is full"):
        next_moved_position(_moved_scenario(2), ws)


def test_next_moved_position_degenerate_region_errors() -> None:
    ws = load_workspace("default")
    ws.moved_region = np.array([80.0, 5.0, 1.0, 3.0])  # spacing 2 -> num_cols 0

    with pytest.raises(ValueError, match="Region is full"):
        next_moved_position(_moved_scenario(0), ws)
    with pytest.raises(ValueError, match="Moved region is full"):
        next_moved_position(_moved_scenario(2), ws)
