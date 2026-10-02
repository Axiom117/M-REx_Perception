"""Simulation state enums (string values must match MATLAB exactly).

Ported from the string literals used across ``src/**/*.m``; keep the values
identical so logs and MATLAB/Python cross-checks stay comparable.
"""

from __future__ import annotations

from enum import StrEnum


class EmbryoState(StrEnum):
    """Embryo lifecycle states."""

    FREE = "free"
    CLUSTERED = "clustered"
    SELECTED = "selected"
    GRASPED = "grasped"
    MOVED = "moved"
    FAILED = "failed"


class ToolState(StrEnum):
    """Tool head states.

    ``LIFTED`` / ``CONTACT`` / ``PLACE_CONTACT`` are legacy states used only by
    ``raiseTool.m`` / ``lowerTool*.m`` (not part of the main loop); they are
    kept for fidelity with the MATLAB implementation.
    """

    HOME = "home"
    ABOVE_EMBRYO = "aboveEmbryo"
    GRASPED = "grasped"
    FAILED_GRASP = "failedGrasp"
    ABOVE_MOVED_POSITION = "aboveMovedPosition"
    RELEASED = "released"
    # legacy states (kept for fidelity; the main loop does not use them)
    LIFTED = "lifted"
    CONTACT = "contact"
    PLACE_CONTACT = "placeContact"
