"""Export a composite PNG of the three orthographic views."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
from PySide6.QtGui import QImage
from pyvistaqt import QtInteractor

_BACKGROUND = (0x16, 0x18, 0x1D)


def save_three_view_png(path: str | Path, plotters: Iterable[QtInteractor]) -> Path:
    """Render each plotter and write them side by side into one PNG."""
    images = [_render_rgb(plotter) for plotter in plotters]
    height = max(image.shape[0] for image in images)

    padded: list[np.ndarray] = []
    for image in images:
        if image.shape[0] < height:
            pad = np.empty((height - image.shape[0], image.shape[1], 3), dtype=np.uint8)
            pad[:] = _BACKGROUND
            image = np.vstack([image, pad])
        padded.append(np.ascontiguousarray(image))

    composite = np.hstack(padded)
    height, width, _ = composite.shape
    png = QImage(composite.tobytes(), width, height, 3 * width, QImage.Format.Format_RGB888)

    path = Path(path)
    if not png.save(str(path)):
        raise OSError(f"Could not write image: {path}")
    return path


def _render_rgb(plotter: QtInteractor) -> np.ndarray:
    image = plotter.screenshot(return_img=True)
    if image is None:
        raise RuntimeError("plotter screenshot returned no image")
    return _as_rgb(image)


def _as_rgb(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image)
    if image.ndim == 2:
        image = np.dstack([image] * 3)
    return image[..., :3]
