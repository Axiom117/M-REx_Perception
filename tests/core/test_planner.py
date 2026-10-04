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


def test_has_free_embryos() -> None:
    assert has_free_embryos([_embryo(1), _embryo(2, EmbryoState.CLUSTERED)])
    assert not has_free_embryos(
        [_embryo(1, EmbryoState.CLUSTERED), _embryo(2, EmbryoState.MOVED)]
    )
    assert not has_free_embryos([])


def test_select_nearest_free() -> None:
    clustered = _embryo(1, EmbryoState.CLUSTERED, (49.0, 50.0, 0.1))
    nearest = _embryo(2, EmbryoState.FREE, (40.0, 50.0, 0.1))
    farther = _embryo(3, EmbryoState.FREE, (10.0, 10.0, 0.1))
    previous = _embryo(4, EmbryoState.SELECTED, (45.0, 50.0, 0.1))
    embryos = [clustered, nearest, farther, previous]

    result = select_nearest_free(embryos, TARGET)

    assert result is embryos
    assert nearest.state == EmbryoState.SELECTED  # only free candidates, nearest wins
    assert farther.state == EmbryoState.FREE
    assert clustered.state == EmbryoState.CLUSTERED  # non-free never selected
    assert previous.state == EmbryoState.FREE  # previous selection was reset

    # nothing free left -> warn and leave states untouched
    idle = [_embryo(1, EmbryoState.CLUSTERED), _embryo(2, EmbryoState.MOVED)]
    with pytest.warns(UserWarning, match="No embryos left to select"):
        result = select_nearest_free(idle, TARGET)
    assert result is idle
    assert [e.state for e in idle] == [EmbryoState.CLUSTERED, EmbryoState.MOVED]


def test_select_embryo_is_one_based_and_resets_others() -> None:
    embryos = [_embryo(1, EmbryoState.SELECTED), _embryo(2), _embryo(3)]

    select_embryo(embryos, 3)

    assert [e.state for e in embryos] == [
        EmbryoState.FREE,
        EmbryoState.FREE,
        EmbryoState.SELECTED,
    ]


def test_next_moved_position_grid() -> None:
    ws = load_workspace("default")  # spacing = 0.5 * 4 = 2; num_cols = floor(100 / 2) = 50

    assert next_moved_position(_moved_scenario(0), ws) == pytest.approx([81.0, 6.0, 0.1])
    assert next_moved_position(_moved_scenario(1), ws) == pytest.approx([83.0, 6.0, 0.1])
    assert next_moved_position(_moved_scenario(49), ws) == pytest.approx([179.0, 6.0, 0.1])
    assert next_moved_position(_moved_scenario(50), ws) == pytest.approx([81.0, 8.0, 0.1])

    # grid dimensions come from the first embryo (spacing 0.25 * 4 = 1.0)
    embryos = _moved_scenario(0)
    embryos[0].length = 0.25
    embryos[0].height = 0.4
    assert next_moved_position(embryos, ws) == pytest.approx([80.5, 5.5, 0.2])


def test_next_moved_position_errors() -> None:
    ws = load_workspace("default")
    ws.moved_region = np.array([80.0, 5.0, 4.0, 3.0])  # spacing 2 -> num_cols 2, height 3
    with pytest.raises(ValueError, match="Moved region is full"):
        next_moved_position(_moved_scenario(2), ws)

    ws.moved_region = np.array([80.0, 5.0, 1.0, 3.0])  # spacing 2 -> num_cols 0
    with pytest.raises(ValueError, match="Region is full"):
        next_moved_position(_moved_scenario(0), ws)
    with pytest.raises(ValueError, match="Moved region is full"):
        next_moved_position(_moved_scenario(2), ws)
