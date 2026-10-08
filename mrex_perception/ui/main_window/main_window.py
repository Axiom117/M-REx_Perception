"""Main application window: menu bar, dashboard, multi-viewport panel, status bar.

The layout lives in ``main_window.ui`` (edit it with Qt Designer); this module
is the run controller: it builds one worker per run, pumps the latest snapshot
into the views and dashboard, exports screenshots and keeps UI state in sync
with the worker signals.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pyvista as pv
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QFileDialog, QLabel, QMainWindow, QMessageBox, QWidget

from mrex_perception import __version__
from mrex_perception.config.app import AppConfig, load_app_config
from mrex_perception.config.workspace import list_workspace_configs
from mrex_perception.core.engine import EngineParams, EngineResult, FinishReason, Snapshot
from mrex_perception.core.models import EmbryoState, Workspace
from mrex_perception.core.setup import populate_random
from mrex_perception.ui.screenshot import save_three_view_png
from mrex_perception.ui.worker import SimulationWorker

from .ui_main_window import Ui_MainWindow

_TICK_MS = 16  # snapshot pump (~60 Hz)
_UI_REFRESH_SECONDS = 0.25  # dashboard text refresh; per-frame Qt repaints throttle macOS/VTK swaps


class MainWindow(QMainWindow):
    """Top-level window and run controller."""

    def __init__(self, config: AppConfig | None = None, parent: QWidget | None = None) -> None:
        # Initialize the C++ Qt main window via the parent class constructor.
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

        # Config injection ("A" scheme): entry points pass a pre-loaded AppConfig
        # aggregate; new config sections grow inside AppConfig, never in this
        # signature. The None fallback keeps bare ``MainWindow()`` usable (tests).
        self._config = config if config is not None else load_app_config()
        self._config_names: list[str] = []
        self.viewports.set_workspace(self._config.workspace)

        self._worker: SimulationWorker | None = None
        self._paused = False
        self._last_snapshot: Snapshot | None = None
        self.last_result: EngineResult | None = None

        self._frames = 0
        self._fps_since = time.monotonic()
        self._ui_since = 0.0

        self._build_status_bar()
        self._wire_actions()
        self._build_config_menu()
        self._sync_actions()
        self.statusBar().showMessage("READY")

        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._pump)
        self._timer.start()

    # -- public API (also used by tests) -------------------------------------

    @property
    def workspace(self) -> Workspace:
        """Active workspace (from the injected/loaded app config)."""
        return self._config.workspace

    def is_running(self) -> bool:
        return self._worker is not None

    def apply_config(self, config: AppConfig) -> bool:
        """Switch the app config at runtime (Config menu entry point).

        Ignored while a run is active: the worker holds the current workspace.
        On success the static scene is rebuilt and previous run telemetry is
        cleared; the next run derives embryos and tool head from the new config.
        """
        if self._worker is not None:
            self.statusBar().showMessage("CANNOT SWITCH CONFIG WHILE RUNNING")
            return False
        self._config = config
        self.viewports.set_workspace(config.workspace)
        self.reset_run()
        return True

    def start_run(self) -> None:
        """Build embryos + tool and start a fresh worker run."""
        if self._worker is not None:
            return
        rng = np.random.default_rng(self.dashboard.seed)
        embryos = populate_random(
            self.dashboard.count, self._config.workspace, rng, self._config.embryo
        )
        params = EngineParams(
            num_steps=self.dashboard.num_steps, target_point=self.dashboard.target_point
        )
        worker = SimulationWorker(
            self._config.workspace,
            embryos,
            params,
            rng=rng,
            tool=self._config.tool.to_tool_head(self._config.workspace),
            cluster_threshold=self._config.embryo.cluster_threshold,
        )
        worker.runFinished.connect(self._on_run_finished)
        worker.failed.connect(self._on_run_failed)
        worker.finished.connect(self._on_thread_finished)
        self._worker = worker
        self._last_snapshot = None
        self.last_result = None
        self.dashboard.begin_run()
        self._sync_actions()
        self.statusBar().showMessage("RUNNING…")
        worker.start()

    def toggle_pause(self) -> None:
        if self._worker is None:
            return
        self._paused = not self._paused
        self._worker.request_pause(self._paused)
        self.dashboard.set_paused(self._paused)
        self._sync_actions()
        self.statusBar().showMessage("PAUSED (Step)" if self._paused else "RUNNING…")

    def step_run(self) -> None:
        if self._worker is not None and self._paused:
            self._worker.request_step()

    def stop_run(self) -> None:
        if self._worker is None:
            return
        self._worker.request_stop()
        self.statusBar().showMessage("STOPPING…")

    def reset_run(self) -> None:
        """Clear scene, telemetry and charts back to the initial state."""
        if self._worker is not None:
            return
        self._last_snapshot = None
        self.last_result = None
        self.viewports.clear_scene()
        self.dashboard.reset_display()
        self._step_label.setText("Step 0")
        self._tool_label.setText("tool —")
        self.statusBar().showMessage("READY")

    def export_image(self, path: str | Path) -> Path:
        """Save a composite PNG of the three views and report it in the status bar."""
        saved = save_three_view_png(
            path, (self.viewports.top, self.viewports.front, self.viewports.right)
        )
        self.statusBar().showMessage(f"IMAGE SAVED: {saved}")
        return saved

    # -- window / worker events ----------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        self._timer.stop()
        if self._worker is not None:
            self._worker.request_stop()
            self._worker.wait(1500)  # stop is prompt; proceed with exit regardless
        self.viewports.close_plotters()
        super().closeEvent(event)

    def _pump(self) -> None:
        """Render the latest snapshot into the views (latest-wins).

        The 3D views follow every snapshot for smooth animation; the dashboard
        text/charts refresh at ``_UI_REFRESH_SECONDS`` so per-frame Qt repaints
        do not fight the VTK swap chains (macOS).
        """
        if self._worker is None:
            return
        snapshot = self._worker.take_snapshot()
        if snapshot is None or snapshot is self._last_snapshot:
            return
        self._last_snapshot = snapshot
        self.viewports.update_scene(snapshot)
        self.dashboard.add_sample(snapshot)
        self._frames += 1

        now = time.monotonic()
        if now - self._ui_since >= _UI_REFRESH_SECONDS:
            self._ui_since = now
            self.dashboard.update_live(snapshot)
            self._step_label.setText(f"Step {snapshot.step_index}")
            position = snapshot.tool.position
            self._tool_label.setText(
                f"tool [{position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}]"
            )
        if now - self._fps_since >= 1.0:
            self._fps_label.setText(f"FPS {round(self._frames / (now - self._fps_since))}")
            self._frames = 0
            self._fps_since = now

    def _on_run_finished(self, result: EngineResult) -> None:
        self.last_result = result
        self.dashboard.finish(result)
        if result.finish_reason == FinishReason.STOPPED:
            self.statusBar().showMessage("STOPPED (NO RESET, NO SUMMARY)")
        else:
            moved = sum(1 for e in result.embryos if e.state == EmbryoState.MOVED)
            self.statusBar().showMessage(f"FINISHED · moved {moved}/{len(result.embryos)}")

    def _on_run_failed(self, message: str) -> None:
        self.statusBar().showMessage("运行失败")
        QMessageBox.warning(self, "仿真失败", message)

    def _on_thread_finished(self) -> None:
        worker = self._worker
        if worker is not None:
            worker.deleteLater()
            self._worker = None
        self._paused = False
        self.dashboard.set_running(False)
        self._sync_actions()

    # -- UI wiring -----------------------------------------------------------

    def _wire_actions(self) -> None:
        ui = self.ui
        ui.actionQuit.triggered.connect(self.close)
        ui.actionStart.triggered.connect(self.start_run)
        ui.actionPause.triggered.connect(self.toggle_pause)
        ui.actionStep.triggered.connect(self.step_run)
        ui.actionStop.triggered.connect(self.stop_run)
        ui.actionReset.triggered.connect(self.reset_run)
        ui.actionFitAll.triggered.connect(self.viewports.fit_all)
        ui.actionResetView.triggered.connect(self.viewports.reset_views)
        ui.actionShowIds.toggled.connect(self.viewports.set_show_ids)
        ui.actionShowArrows.toggled.connect(self.viewports.set_show_arrows)
        ui.actionExportImage.triggered.connect(self._choose_export_image)
        ui.actionAbout.triggered.connect(self._show_about)

        self.dashboard.startRequested.connect(self.start_run)
        self.dashboard.pauseRequested.connect(self.toggle_pause)
        self.dashboard.stepRequested.connect(self.step_run)
        self.dashboard.stopRequested.connect(self.stop_run)
        self.dashboard.resetRequested.connect(self.reset_run)

    def _build_config_menu(self) -> None:
        """Populate the Config menu with the available workspace YAMLs."""
        self._config_names = list_workspace_configs()
        if not self._config_names:
            self.ui.menuConfig.setToolTip("未找到 config/workspace/*.yaml")
            return
        for name in self._config_names:
            action = self.ui.menuConfig.addAction(name)
            action.triggered.connect(lambda _checked=False, n=name: self._select_config(n))

    def _select_config(self, name: str) -> None:
        """Load a workspace config by name and apply it (Config menu handler)."""
        try:
            config = load_app_config(name)
        except (FileNotFoundError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "配置加载失败", str(exc))
            return
        if self.apply_config(config):
            self.statusBar().showMessage(f"已应用配置：{name}")

    def _sync_actions(self) -> None:
        running = self._worker is not None
        self.ui.actionStart.setEnabled(not running)
        self.ui.actionPause.setEnabled(running)
        self.ui.actionStop.setEnabled(running)
        self.ui.actionStep.setEnabled(running and self._paused)
        self.ui.actionReset.setEnabled(not running)
        self.ui.menuConfig.setEnabled(not running and bool(self._config_names))

    def _build_status_bar(self) -> None:
        bar = self.statusBar()
        self._step_label = QLabel("步 0")
        self._tool_label = QLabel("tool —")
        self._fps_label = QLabel("FPS —")
        for label in (self._step_label, self._tool_label, self._fps_label):
            bar.addPermanentWidget(label)
        # versionLabel is declared in main_window.ui; adopt it as a permanent
        # widget so it stays visible next to transient status messages.
        bar.addPermanentWidget(self.ui.versionLabel)
        self.ui.versionLabel.setText(f"PyVista {pv.__version__} · v{__version__}")

    def _choose_export_image(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出截图", "mrex_scene.png", "PNG (*.png)")
        if path:
            self.export_image(path)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "关于 M-REx Perception",
            f"<b>M-REx Perception</b> v{__version__}<br>"
            "Python 全栈迁移 — M4 GUI（仿真）<br><br>"
            "PySide6 + PyVista (VTK) + pyqtgraph",
        )

