"""Simulation summary statistics (port of ``src/reporting/simulationSummary.m``).

``compute_summary`` returns a :class:`SummaryReport` whose fields map 1:1 to
the numbers printed by ``simulationSummary.m`` (fprintf formatting stays in
the presentation layer). Branch structure is kept faithful, including the
quirk that the yaw-adjustment max/mean are only derived from
``move_yaw_changes`` when there are at least two rotation samples.
Clustered embryos are not counted in any bucket (MATLAB behavior); only the
implicit ``total - moved - failed - free - selected - grasped`` differs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from mrex_perception.core.models import Embryo
from mrex_perception.core.motion_log import MotionLog
from mrex_perception.core.states import EmbryoState

_MOTION_EPS = 1e-9


@dataclass(eq=False)
class SummaryReport:
    """Numeric summary (see class field names vs ``simulationSummary.m``)."""

    # counts
    total: int
    moved: int
    grasped: int
    selected: int
    failed: int
    free: int
    total_attempts: int
    successful_pickups: int
    average_attempts: float
    success_rate: float  # percent, denominator moved + failed
    # tool motion - position
    num_motion_samples: int
    start_position: np.ndarray  # (3,)
    final_position: np.ndarray  # (3,)
    minimum_position: np.ndarray  # (3,)
    maximum_position: np.ndarray  # (3,)
    position_range: np.ndarray  # (3,)
    total_tool_distance: float
    minimum_segment_distance: float
    maximum_segment_distance: float
    average_segment_distance: float
    # tool motion - rotation (degrees)
    num_rotation_samples: int
    minimum_rotation_deg: np.ndarray  # (3,)
    maximum_rotation_deg: np.ndarray  # (3,)
    rotation_range_deg: np.ndarray  # (3,)
    net_rotation_deg: np.ndarray  # (3,)
    cumulative_rotation_deg: np.ndarray  # (3,)
    total_angular_motion_deg: float
    maximum_yaw_adjustment_deg: float
    average_yaw_adjustment_deg: float

    def to_dict(self) -> dict[str, Any]:
        """Plain-python snapshot (JSON ready) for reports / exports."""
        return {
            "total": self.total,
            "moved": self.moved,
            "grasped": self.grasped,
            "selected": self.selected,
            "failed": self.failed,
            "free": self.free,
            "total_attempts": self.total_attempts,
            "successful_pickups": self.successful_pickups,
            "average_attempts": self.average_attempts,
            "success_rate": self.success_rate,
            "num_motion_samples": self.num_motion_samples,
            "start_position": self.start_position.tolist(),
            "final_position": self.final_position.tolist(),
            "minimum_position": self.minimum_position.tolist(),
            "maximum_position": self.maximum_position.tolist(),
            "position_range": self.position_range.tolist(),
            "total_tool_distance": self.total_tool_distance,
            "minimum_segment_distance": self.minimum_segment_distance,
            "maximum_segment_distance": self.maximum_segment_distance,
            "average_segment_distance": self.average_segment_distance,
            "num_rotation_samples": self.num_rotation_samples,
            "minimum_rotation_deg": self.minimum_rotation_deg.tolist(),
            "maximum_rotation_deg": self.maximum_rotation_deg.tolist(),
            "rotation_range_deg": self.rotation_range_deg.tolist(),
            "net_rotation_deg": self.net_rotation_deg.tolist(),
            "cumulative_rotation_deg": self.cumulative_rotation_deg.tolist(),
            "total_angular_motion_deg": self.total_angular_motion_deg,
            "maximum_yaw_adjustment_deg": self.maximum_yaw_adjustment_deg,
            "average_yaw_adjustment_deg": self.average_yaw_adjustment_deg,
        }


def compute_summary(embryos: list[Embryo], motion_log: MotionLog) -> SummaryReport:
    """Compute the simulation summary (port of ``simulationSummary.m``)."""
    states = [e.state for e in embryos]

    total = len(embryos)
    moved = sum(1 for s in states if s == EmbryoState.MOVED)
    grasped = sum(1 for s in states if s == EmbryoState.GRASPED)
    selected = sum(1 for s in states if s == EmbryoState.SELECTED)
    failed = sum(1 for s in states if s == EmbryoState.FAILED)
    free = sum(1 for s in states if s == EmbryoState.FREE)

    total_attempts = int(sum(e.attempts for e in embryos))
    successful_pickups = int(sum(bool(e.picked_successfully) for e in embryos))
    average_attempts = total_attempts / total if total > 0 else 0.0
    success_rate = 100.0 * moved / (moved + failed) if (moved + failed) > 0 else 0.0

    # -- positions ---------------------------------------------------------
    positions = motion_log.positions
    num_motion_samples = int(positions.shape[0])

    if num_motion_samples >= 2:
        segment_distances = np.linalg.norm(np.diff(positions, axis=0), axis=1)
        moving_segments = segment_distances[segment_distances > _MOTION_EPS]

        total_tool_distance = float(np.sum(segment_distances))
        if moving_segments.size > 0:
            minimum_segment_distance = float(np.min(moving_segments))
            maximum_segment_distance = float(np.max(moving_segments))
            average_segment_distance = float(np.mean(moving_segments))
        else:
            minimum_segment_distance = 0.0
            maximum_segment_distance = 0.0
            average_segment_distance = 0.0
    else:
        total_tool_distance = 0.0
        minimum_segment_distance = 0.0
        maximum_segment_distance = 0.0
        average_segment_distance = 0.0

    if num_motion_samples > 0:
        start_position = positions[0].copy()
        final_position = positions[-1].copy()
        minimum_position = np.min(positions, axis=0)
        maximum_position = np.max(positions, axis=0)
        position_range = maximum_position - minimum_position
    else:
        start_position = np.zeros(3)
        final_position = np.zeros(3)
        minimum_position = np.zeros(3)
        maximum_position = np.zeros(3)
        position_range = np.zeros(3)

    # -- rotations ---------------------------------------------------------
    rotation = motion_log.rotation
    num_rotation_samples = int(rotation.shape[0])

    if num_rotation_samples >= 2:
        unwrapped_rotation = np.unwrap(rotation, axis=0)
        rotation_differences = np.diff(unwrapped_rotation, axis=0)

        moving_yaw_changes = motion_log.move_yaw_changes
        moving_yaw_changes = moving_yaw_changes[moving_yaw_changes > _MOTION_EPS]
        if moving_yaw_changes.size > 0:
            maximum_yaw_adjustment = float(np.max(moving_yaw_changes))
            average_yaw_adjustment = float(np.mean(moving_yaw_changes))
        else:
            maximum_yaw_adjustment = 0.0
            average_yaw_adjustment = 0.0

        cumulative_rotation = np.sum(np.abs(rotation_differences), axis=0)
        net_rotation = unwrapped_rotation[-1] - unwrapped_rotation[0]
        minimum_rotation = np.min(unwrapped_rotation, axis=0)
        maximum_rotation = np.max(unwrapped_rotation, axis=0)
        rotation_range = maximum_rotation - minimum_rotation
        angular_step_magnitude = np.linalg.norm(rotation_differences, axis=1)
        total_angular_motion = float(np.sum(angular_step_magnitude))
    elif num_rotation_samples == 1:
        maximum_yaw_adjustment = 0.0
        average_yaw_adjustment = 0.0
        cumulative_rotation = np.zeros(3)
        net_rotation = np.zeros(3)
        minimum_rotation = rotation[0].copy()
        maximum_rotation = rotation[0].copy()
        rotation_range = np.zeros(3)
        total_angular_motion = 0.0
    else:
        maximum_yaw_adjustment = 0.0
        average_yaw_adjustment = 0.0
        cumulative_rotation = np.zeros(3)
        net_rotation = np.zeros(3)
        minimum_rotation = np.zeros(3)
        maximum_rotation = np.zeros(3)
        rotation_range = np.zeros(3)
        total_angular_motion = 0.0

    return SummaryReport(
        total=total,
        moved=moved,
        grasped=grasped,
        selected=selected,
        failed=failed,
        free=free,
        total_attempts=total_attempts,
        successful_pickups=successful_pickups,
        average_attempts=average_attempts,
        success_rate=success_rate,
        num_motion_samples=num_motion_samples,
        start_position=start_position,
        final_position=final_position,
        minimum_position=minimum_position,
        maximum_position=maximum_position,
        position_range=position_range,
        total_tool_distance=total_tool_distance,
        minimum_segment_distance=minimum_segment_distance,
        maximum_segment_distance=maximum_segment_distance,
        average_segment_distance=average_segment_distance,
        num_rotation_samples=num_rotation_samples,
        minimum_rotation_deg=np.rad2deg(minimum_rotation),
        maximum_rotation_deg=np.rad2deg(maximum_rotation),
        rotation_range_deg=np.rad2deg(rotation_range),
        net_rotation_deg=np.rad2deg(net_rotation),
        cumulative_rotation_deg=np.rad2deg(cumulative_rotation),
        total_angular_motion_deg=float(np.rad2deg(total_angular_motion)),
        maximum_yaw_adjustment_deg=float(np.rad2deg(maximum_yaw_adjustment)),
        average_yaw_adjustment_deg=float(np.rad2deg(average_yaw_adjustment)),
    )
