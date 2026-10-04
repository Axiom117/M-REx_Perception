"""Setup layer tests: embryo placement/detection/clustering + tool head (M1)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from mrex_perception.config.workspace import REQUIRED_FIELDS, WorkspaceConfig, load_workspace
from mrex_perception.core.math import rotation_z
from mrex_perception.core.models import Embryo, EmbryoState, ToolState
from mrex_perception.core.setup import (
    create_tool_head,
    from_detections,
    mark_clustered,
    populate_random,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture()
def workspace():
    return load_workspace("default")


# -- populate_random ---------------------------------------------------------


def test_populate_random_count_and_defaults(workspace) -> None:
    embryos = populate_random(6, workspace, np.random.default_rng(42))
    assert [e.id for e in embryos] == [1, 2, 3, 4, 5, 6]
    for e in embryos:
        assert e.position[2] == pytest.approx(0.1)
        assert e.state == EmbryoState.FREE
        assert e.attempts == 0


def test_populate_random_inside_source_region(workspace) -> None:
    embryos = populate_random(6, workspace, np.random.default_rng(42))
    source_x, source_y, source_w, source_h = workspace.source_region
    for e in embryos:
        assert source_x <= e.position[0] <= source_x + source_w
        assert source_y <= e.position[1] <= source_y + source_h


def test_populate_random_min_spacing(workspace) -> None:
    embryos = populate_random(6, workspace, np.random.default_rng(0))
    for i, a in enumerate(embryos):
        for b in embryos[i + 1 :]:
            assert np.linalg.norm(a.position - b.position) >= 1.0


def test_populate_random_seed_reproducible(workspace) -> None:
    first = populate_random(6, workspace, np.random.default_rng(7))
    second = populate_random(6, workspace, np.random.default_rng(7))
    for a, b in zip(first, second, strict=True):
        assert np.array_equal(a.position, b.position)
        assert np.array_equal(a.orientation, b.orientation)


def test_populate_random_orientation_is_rz(workspace) -> None:
    for e in populate_random(20, workspace, np.random.default_rng(3)):
        yaw = np.arctan2(e.orientation[1, 0], e.orientation[0, 0])
        assert e.orientation == pytest.approx(rotation_z(yaw))
        assert e.pose[:3, 3] == pytest.approx(e.position)


# -- mark_clustered ----------------------------------------------------------


def test_mark_clustered_near_pair_far_free() -> None:
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


def test_mark_clustered_threshold_is_strict() -> None:
    a = Embryo(id=1, position=np.array([0.0, 0.0, 0.1]))
    b = Embryo(id=2, position=np.array([1.0, 0.0, 0.1]))
    mark_clustered([a, b])
    assert not a.is_clustered and not b.is_clustered


def test_mark_clustered_resets_flag_but_not_state() -> None:
    # MATLAB behavior: isClustered is reset every call, `state` is not touched.
    a = Embryo(
        id=1,
        position=np.array([0.0, 0.0, 0.1]),
        is_clustered=True,
        state=EmbryoState.CLUSTERED,
    )
    b = Embryo(id=2, position=np.array([10.0, 0.0, 0.1]))
    mark_clustered([a, b])
    assert not a.is_clustered
    assert a.state == EmbryoState.CLUSTERED


# -- from_detections ---------------------------------------------------------


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


def test_from_detections_filters_low_confidence(workspace) -> None:
    records = [_record(confidence=0.9), _record(confidence=0.5, x=100.0)]
    embryos = from_detections(records, workspace)
    assert len(embryos) == 1
    assert embryos[0].id == 1
    assert embryos[0].confidence == pytest.approx(0.9)


def test_from_detections_maps_position_and_yaw(workspace) -> None:
    theta = 0.3
    embryo = from_detections([_record(theta=theta)], workspace)[0]
    assert embryo.position == pytest.approx([10.0, 17.5, 0.1])
    assert embryo.orientation == pytest.approx(rotation_z(-theta))


def test_from_detections_empty_warns(workspace) -> None:
    with pytest.warns(UserWarning, match="No embryos detected"):
        assert from_detections([_record(confidence=0.1)], workspace) == []


# -- scenario fixture --------------------------------------------------------


def _load_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "scenario_basic.json").read_text(encoding="utf-8"))


def test_fixture_workspace_matches_default() -> None:
    data = _load_fixture()
    assert set(REQUIRED_FIELDS) <= set(data["workspace"])
    fixture_ws = WorkspaceConfig.model_validate(data["workspace"]).to_workspace()
    default_ws = load_workspace("default")
    assert np.array_equal(fixture_ws.size, default_ws.size)
    assert np.array_equal(fixture_ws.source_region, default_ws.source_region)
    assert np.array_equal(fixture_ws.moved_region, default_ws.moved_region)


def test_fixture_embryos_explicit_and_spaced() -> None:
    embryos = _load_fixture()["embryos"]
    assert len(embryos) == 6
    valid_states = {state.value for state in EmbryoState}
    for i, e in enumerate(embryos):
        assert e["id"] == i + 1
        assert e["state"] in valid_states
        assert e["position"][2] == pytest.approx(0.1)
        assert 0.0 <= e["yaw"] < 2 * np.pi
    positions = [np.asarray(e["position"]) for e in embryos]
    for i, p in enumerate(positions):
        for q in positions[i + 1 :]:
            assert np.linalg.norm(p - q) >= 1.0


# -- tool head (create_tool_head) -------------------------------------------


def test_tool_specs() -> None:
    tool = create_tool_head(load_workspace("default"))
    assert tool.name == "adhesionTool"
    assert tool.contact_radius == pytest.approx(0.25)
    assert tool.diameter == pytest.approx(1.5)
    assert tool.radius == pytest.approx(0.75)
    assert tool.height == pytest.approx(0.5)
    assert tool.clearance == pytest.approx(1.0)
    assert tool.shape == "cylinder"
    assert tool.adhesion_model == "vanDerWaalsDroplet"


def test_tool_initial_position_and_state() -> None:
    tool = create_tool_head(load_workspace("default"))
    # source region is [0, 5, ...] -> [0/2 + 15, 5/2 + 15, 10]
    assert tool.position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.home_position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.target_position == pytest.approx([15.0, 17.5, 10.0])
    assert tool.state == ToolState.HOME
    assert not tool.has_embryo
    assert tool.attached_embryo_id == 0
    assert tool.velocity == pytest.approx(0.0)
    assert tool.max_velocity == pytest.approx(10.0)
    assert tool.path == []


def test_pose_assembly() -> None:
    tool = create_tool_head(load_workspace("default"))
    tool.position = np.array([1.0, 2.0, 3.0])
    tool.orientation = rotation_z(0.25)
    pose = tool.pose
    assert pose[:3, :3] == pytest.approx(rotation_z(0.25))
    assert pose[:3, 3] == pytest.approx([1.0, 2.0, 3.0])
    assert pose[3] == pytest.approx([0.0, 0.0, 0.0, 1.0])
