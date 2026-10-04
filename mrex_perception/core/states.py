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

    ``LIFTED`` is set by ``raise_tool`` (the failed-grasp path of the main
    loop); ``CONTACT`` / ``PLACE_CONTACT`` come from the legacy ``lowerTool*.m``
    files, which are kept for fidelity but never wired into the engine.
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
