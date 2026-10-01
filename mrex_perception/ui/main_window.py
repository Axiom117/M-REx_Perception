"""Main application window: menu bar, dashboard, multi-viewport panel, status bar."""

from __future__ import annotations

import pyvista as pv
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QWidget

from mrex_perception import __version__
from mrex_perception.ui.dashboard import DashboardPanel
from mrex_perception.ui.viewport import MultiViewPanel


class MainWindow(QMainWindow):
    """Top-level window (M0 shell: viewports + placeholder dashboard)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("M-REx Perception")
        self.resize(1500, 900)

        self.viewports = MultiViewPanel(self)
        self.dashboard = DashboardPanel(self)

        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        layout.addWidget(self.dashboard)
        layout.addWidget(self.viewports, 1)
        self.setCentralWidget(central)

        self._create_menus()

        self.statusBar().showMessage("就绪 · M0 骨架（仿真核心 M1 起接入）")
        self.statusBar().addPermanentWidget(QLabel(f"PyVista {pv.__version__} · v{__version__}"))

    # -- menus ---------------------------------------------------------------

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("文件(&F)")
        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Placeholder entries; wired to the simulation engine in M4.
        run_menu = self.menuBar().addMenu("运行(&R)")
        for text in ("Start", "Pause", "Step", "Stop", "Reset"):
            action = QAction(text, self)
            action.setEnabled(False)
            action.setStatusTip("M4 接入仿真引擎后启用")
            run_menu.addAction(action)

        view_menu = self.menuBar().addMenu("视图(&V)")
        fit_action = QAction("Fit All", self)
        fit_action.setShortcut("F")
        fit_action.triggered.connect(self.viewports.fit_all)
        view_menu.addAction(fit_action)

        reset_action = QAction("复位视角", self)
        reset_action.setShortcut("0")
        reset_action.triggered.connect(self.viewports.reset_views)
        view_menu.addAction(reset_action)

        help_menu = self.menuBar().addMenu("帮助(&H)")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "关于 M-REx Perception",
            f"<b>M-REx Perception</b> v{__version__}<br>"
            "Python 全栈迁移 — M0 骨架<br><br>"
            "PySide6 + PyVista (VTK) + pyqtgraph",
        )
