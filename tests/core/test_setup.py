"""Setup layer tests: embryo placement/detection/clustering (M1)."""

from __future__ import annotations

import numpy as np
import pytest

from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import Embryo, EmbryoState
from mrex_perception.core.setup import from_detections, mark_clustered, populate_random


def test_populate_random_placement_and_defaults() -> None:
    ws = load_workspace("default")
    embryos = populate_random(6, ws, np.random.default_rng(42))
    assert [e.id for e in embryos] == [1, 2, 3, 4, 5, 6]
    source_x, source_y, source_w, source_h = ws.source_region
    for e in embryos:
        assert source_x <= e.position[0] <= source_x + source_w
        assert source_y <= e.position[1] <= source_y + source_h
        assert e.position[2] == pytest.approx(0.1)
        assert e.state == EmbryoState.FREE
        assert e.attempts == 0
        assert e.pose[:3, 3] == pytest.approx(e.position)
        yaw = np.arctan2(e.orientation[1, 0], e.orientation[0, 0])
        assert e.orientation == pytest.approx(rotation_z(yaw))


def test_populate_random_spacing_and_reproducibility() -> None:
    ws = load_workspace("default")
    first = populate_random(6, ws, np.random.default_rng(0))
    for i, a in enumerate(first):
        for b in first[i + 1 :]:
            assert np.linalg.norm(a.position - b.position) >= 1.0

    again = populate_random(6, ws, np.random.default_rng(0))
    for a, b in zip(first, again, strict=True):
        assert np.array_equal(a.position, b.position)
        assert np.array_equal(a.orientation, b.orientation)


def test_mark_clustered() -> None:
    near_a = Embryo(id=1, position=np.array([5.0, 5.0, 0.1]))
    near_b = Embryo(id=2, position=np.array([5.5, 5.0, 0.1]))
    far = Embryo(id=3, position=np.array([10.0, 5.0, 0.1]))
    embryos = [near_a, near_b, far]

    result = mark_clustered(embryos)

    assert result is embryos
    assert near_a.is_clustered and near_b.is_clustered
    assert not far.is_clustered
    assert near_a.state == EmbryoState.CLUSTERED
    assert near_b.state == EmbryoState.CLUSTERED
    assert far.state == EmbryoState.FREE

    # threshold is strict (< 1 mm); flags are reset every call but `state` is not (MATLAB)
    flagged = Embryo(
        id=1,
        position=np.array([0.0, 0.0, 0.1]),
        is_clustered=True,
        state=EmbryoState.CLUSTERED,
    )
    other = Embryo(id=2, position=np.array([1.0, 0.0, 0.1]))
    mark_clustered([flagged, other])
    assert not flagged.is_clustered and not other.is_clustered
    assert flagged.state == EmbryoState.CLUSTERED


def test_from_detections() -> None:
    ws = load_workspace("default")

    # confidence filter >= 0.8
    embryos = from_detections([_record(confidence=0.9), _record(confidence=0.5, x=100.0)], ws)
    assert len(embryos) == 1
    assert embryos[0].id == 1
    assert embryos[0].confidence == pytest.approx(0.9)

    # pixel position mapping and yaw = -theta
    theta = 0.3
    embryo = from_detections([_record(theta=theta)], ws)[0]
    assert embryo.position == pytest.approx([10.0, 17.5, 0.1])
    assert embryo.orientation == pytest.approx(rotation_z(-theta))

    # empty result warns
    with pytest.warns(UserWarning, match="No embryos detected"):
        assert from_detections([_record(confidence=0.1)], ws) == []


def _record(
    confidence: float = 0.9,
    x: float = 500.0,
    y: float = 250.0,
    theta: float = 0.3,
) -> dict:
    return {
        "image": "sample.jpg",
        "image_width": 1000,
        "image_height": 500,
        "class_id": 0,
        "confidence": confidence,
        "x": x,
        "y": y,
        "width": 50.0,
        "height": 40.0,
        "theta": theta,
    }
