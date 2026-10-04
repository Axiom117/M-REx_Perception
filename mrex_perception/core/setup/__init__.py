"""Construction layer: build entities from workspace config or detections."""

from .embryos import from_detections, mark_clustered, populate_random

__all__ = ["from_detections", "mark_clustered", "populate_random"]
