"""Main application window: menu bar, dashboard, multi-viewport panel, status bar.

The layout lives in ``main_window.ui`` (edit it with Qt Designer); this module
keeps only the behaviour wiring: menu connections, status-bar content and the
about dialog.
"""

from __future__ import annotations

import pyvista as pv
from PySide6.QtWidgets import QMainWindow, QMessageBox, QWidget

from mrex_perception import __version__

from .ui_main_window import Ui_MainWindow


class MainWindow(QMainWindow):
    """Top-level window (M0 shell: viewports + placeholder dashboard)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # macOS: by default QMenuBar goes to the system-wide native menu bar
        # (not visible inside the window and not styled by theme.py QSS).
        # Force the in-window menu bar so it matches Designer's preview.
        # self.ui.menubar.setNativeMenuBar(False)

        # Public aliases (kept from the pre-.ui layout).
        self.dashboard = self.ui.dashboard
        self.viewports = self.ui.viewports

        self._wire_actions()
        self._fill_status_bar()

    # -- behaviour wiring -----------------------------------------------------

    def _wire_actions(self) -> None:
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionFitAll.triggered.connect(self.viewports.fit_all)
        self.ui.actionResetView.triggered.connect(self.viewports.reset_views)
        self.ui.actionAbout.triggered.connect(self._show_about)

    def _fill_status_bar(self) -> None:
        bar = self.statusBar()
        bar.showMessage("就绪 · M0 骨架（仿真核心 M1 起接入）")
        # versionLabel is declared in main_window.ui; adopt it as a permanent
        # widget so it stays visible next to transient status messages.
        bar.addPermanentWidget(self.ui.versionLabel)
        self.ui.versionLabel.setText(f"PyVista {pv.__version__} · v{__version__}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "关于 M-REx Perception",
            f"<b>M-REx Perception</b> v{__version__}<br>"
            "Python 全栈迁移 — M0 骨架<br><br>"
            "PySide6 + PyVista (VTK) + pyqtgraph",
        )
