"""Dashboard panel: run controls / embryo source / parameters.

The layout lives in ``dashboard.ui`` (edit it with Qt Designer); this module
only instantiates the generated form class. All controls stay disabled until
the simulation engine (M3) and the UI wiring (M4) land.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from .ui_dashboard import Ui_DashboardPanel


class DashboardPanel(QWidget):
    """Left-hand control panel (placeholder for M4)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_DashboardPanel()
        self.ui.setupUi(self)
