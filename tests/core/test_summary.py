"""Summary statistics aligned with ``simulationSummary.m`` (M2)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from mrex_perception.core.math import make_pose, rotation_z
from mrex_perception.core.models import Embryo, EmbryoState
from mrex_perception.core.reporting import compute_summary
from mrex_perception.core.sim import MotionLog


class _StubTool:
    def __init__(self, pose: np.ndarray) -> None:
        self.pose = pose


def _embryo(
    i: int,
    state: EmbryoState,
    attempts: int = 0,
    picked: bool = False,
) -> Embryo:
    return Embryo(id=i, state=state, attempts=attempts, picked_successfully=picked)


def _record(log: MotionLog, position: tuple[float, float, float], yaw: float = 0.0) -> None:
    pose = make_pose(rotation_z(yaw), np.array(position, dtype=float))
    log.record(_StubTool(pose))


def test_counts_and_rates() -> None:
    embryos = [
        _embryo(1, EmbryoState.MOVED, attempts=1, picked=True),
        _embryo(2, EmbryoState.MOVED, attempts=2, picked=True),
        _embryo(3, EmbryoState.FAILED, attempts=3),
        _embryo(4, EmbryoState.FREE),
        _embryo(5, EmbryoState.SELECTED),
        _embryo(6, EmbryoState.CLUSTERED),  # not counted in any bucket (MATLAB)
    ]

    report = compute_summary(embryos, MotionLog())

    assert (report.total, report.moved, report.failed, report.free) == (6, 2, 1, 1)
    assert (report.grasped, report.selected) == (0, 1)
    assert report.total_attempts == 6
    assert report.successful_pickups == 2
    assert report.average_attempts == pytest.approx(1.0)
    assert report.success_rate == pytest.approx(100 * 2 / 3)

    # to_dict is JSON-serializable for the M3 export
    data = json.loads(json.dumps(report.to_dict()))
    assert data["total"] == 6
    assert data["moved"] == 2
    assert data["success_rate"] == pytest.approx(100 * 2 / 3)


def test_log_edges() -> None:
    report = compute_summary([], MotionLog())
    assert report.total == 0
    assert report.num_motion_samples == 0
    assert report.num_rotation_samples == 0
    assert report.start_position.tolist() == [0.0, 0.0, 0.0]
    assert report.position_range.tolist() == [0.0, 0.0, 0.0]
    assert report.total_tool_distance == 0.0
    assert report.total_angular_motion_deg == 0.0
    assert report.maximum_yaw_adjustment_deg == 0.0

    log = MotionLog()
    _record(log, (1.0, 2.0, 3.0), yaw=0.25)
    report = compute_summary([], log)
    assert report.num_motion_samples == 1
    assert report.start_position == pytest.approx([1.0, 2.0, 3.0])
    assert report.final_position == pytest.approx([1.0, 2.0, 3.0])
    assert report.position_range == pytest.approx([0.0, 0.0, 0.0])
    assert report.total_tool_distance == 0.0
    assert report.minimum_rotation_deg == pytest.approx([0.0, 0.0, np.rad2deg(0.25)])
    assert report.total_angular_motion_deg == 0.0

    # MATLAB quirk: yaw adjustments are only derived with >= 2 rotation samples
    log.record_move_yaw_change(0.5)
    assert compute_summary([], log).maximum_yaw_adjustment_deg == 0.0


def test_position_statistics_ignore_static_segments_for_steps() -> None:
    log = MotionLog()
    _record(log, (0.0, 0.0, 0.0))
    _record(log, (0.0, 0.0, 0.0))  # static segment: contributes to total only
    _record(log, (2.0, 0.0, 0.0))

    report = compute_summary([], log)

    assert report.total_tool_distance == pytest.approx(2.0)
    assert report.minimum_segment_distance == pytest.approx(2.0)
    assert report.maximum_segment_distance == pytest.approx(2.0)
    assert report.average_segment_distance == pytest.approx(2.0)
    assert report.start_position == pytest.approx([0.0, 0.0, 0.0])
    assert report.final_position == pytest.approx([2.0, 0.0, 0.0])
    assert report.minimum_position == pytest.approx([0.0, 0.0, 0.0])
    assert report.maximum_position == pytest.approx([2.0, 0.0, 0.0])
    assert report.position_range == pytest.approx([2.0, 0.0, 0.0])


def test_rotation_statistics_unwrap_and_filter() -> None:
    log = MotionLog()
    _record(log, (0.0, 0.0, 0.0), yaw=np.deg2rad(170.0))
    _record(log, (0.0, 0.0, 0.0), yaw=np.deg2rad(180.0))
    _record(log, (0.0, 0.0, 0.0), yaw=np.deg2rad(-170.0))  # wrapped representation
    log.record_move_yaw_change(1e-12)  # filtered, like MATLAB > 1e-9
    log.record_move_yaw_change(np.deg2rad(20.0))

    report = compute_summary([], log)

    # unwrap across +/-pi: 170 -> 190 degrees, not 170 -> -170
    assert report.minimum_rotation_deg == pytest.approx([0.0, 0.0, 170.0])
    assert report.maximum_rotation_deg == pytest.approx([0.0, 0.0, 190.0])
    assert report.rotation_range_deg == pytest.approx([0.0, 0.0, 20.0])
    assert report.net_rotation_deg == pytest.approx([0.0, 0.0, 20.0])
    assert report.cumulative_rotation_deg == pytest.approx([0.0, 0.0, 20.0])
    assert report.total_angular_motion_deg == pytest.approx(20.0)
    assert report.maximum_yaw_adjustment_deg == pytest.approx(20.0)
    assert report.average_yaw_adjustment_deg == pytest.approx(20.0)
