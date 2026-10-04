"""Image pixel -> workspace coordinate mapping.

Port of ``src/setup/pixelToWorkspace.m``. Generic math helpers (rotations,
poses) live in ``mrex_perception.core.math.transforms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from mrex_perception.core.models import Workspace


def pixel_to_workspace(
    x_pixel: float,
    y_pixel: float,
    image_width: float,
    image_height: float,
    workspace: Workspace,
) -> np.ndarray:
    """Map an image pixel to workspace coordinates (z = 0.1 mm).

    Line-for-line port of ``pixelToWorkspace.m``; the image y axis is flipped
    relative to the workspace y axis. No YOLO dependency: this is pure math and
    is verified against hand-computed samples and MATLAB output (see M1).
    """
    source_x, source_y, source_w, source_h = workspace.source_region
    x = source_x + (x_pixel / image_width) * source_w
    y = source_y + ((image_height - y_pixel) / image_height) * source_h
    return np.array([x, y, 0.1])
