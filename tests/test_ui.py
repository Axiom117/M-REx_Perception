"""M4 UI tests: worker lifecycle + main-window run integration (pytest-qt).

The worker test compares its summary against a direct headless engine run with
the same seed, which is exactly the "GUI data equals CLI data" acceptance
criterion (same code path, same RNG).
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from mrex_perception.config.app import AppConfig, load_app_config
from mrex_perception.config.embryo import load_embryo
from mrex_perception.config.tool_head import load_tool_head
from mrex_perception.config.workspace import load_workspace
from mrex_perception.core.engine import EngineParams, EngineResult, FinishReason, SimulationEngine
from mrex_perception.core.models import ToolHead
from mrex_perception.core.setup import populate_random
from mrex_perception.ui.main_window import MainWindow
from mrex_perception.ui.worker import SimulationWorker

WORKSPACE = load_workspace("default")


def _embryos(seed: int, count: int) -> tuple[np.random.Generator, list]:
    rng = np.random.default_rng(seed)
    return rng, populate_random(count, WORKSPACE, rng)


def _headless_result(seed: int, count: int, steps: int) -> EngineResult:
    rng, embryos = _embryos(seed, count)
    engine = SimulationEngine(
        WORKSPACE,
        embryos,
        EngineParams(num_steps=steps),
        rng=rng,
        tool=ToolHead.for_workspace(WORKSPACE),
    )
    return engine.run()


def _worker(seed: int, count: int, steps: int, step_delay: float) -> SimulationWorker:
    rng, embryos = _embryos(seed, count)
    return SimulationWorker(
        WORKSPACE,
        embryos,
        EngineParams(num_steps=steps),
        rng=rng,
        tool=ToolHead.for_workspace(WORKSPACE),
        step_delay=step_delay,
    )


def test_worker_summary_equals_headless_run(qtbot) -> None:
    worker = _worker(42, 6, 10, step_delay=0.0)
    with qtbot.waitSignal(worker.runFinished, timeout=10_000) as blocker:
        worker.start()
    result = blocker.args[0]
    worker.wait(2000)

    expected = _headless_result(42, 6, 10)
    assert result.finish_reason == expected.finish_reason == FinishReason.COMPLETED
    assert result.summary is not None and expected.summary is not None
    assert result.summary.to_dict() == expected.summary.to_dict()


def test_worker_stop_is_prompt_without_summary(qtbot) -> None:
    worker = _worker(1, 6, 50, step_delay=0.002)
    with qtbot.waitSignal(worker.runFinished, timeout=10_000) as blocker:
        worker.start()
        qtbot.waitUntil(lambda: worker.take_snapshot() is not None, timeout=2000)
        started = time.monotonic()
        worker.request_stop()
    elapsed = time.monotonic() - started
    worker.wait(2000)

    result = blocker.args[0]
    assert result.finish_reason == FinishReason.STOPPED
    assert result.summary is None
    assert elapsed < 0.5  # acceptance: stop is observed within one step


def test_worker_pause_freezes_and_step_advances(qtbot) -> None:
    worker = _worker(3, 1, 50, step_delay=0.002)
    worker.start()
    qtbot.waitUntil(lambda: worker.take_snapshot() is not None, timeout=2000)
    try:
        worker.request_pause(True)
        frozen = _wait_until_frozen(worker, qtbot)
        assert worker.take_snapshot() is frozen  # no progress while paused

        worker.request_step()
        qtbot.waitUntil(lambda: worker.take_snapshot() is not frozen, timeout=1000)
        advanced = worker.take_snapshot()
        assert (advanced.step_index, advanced.phase) != (frozen.step_index, frozen.phase)

        worker.request_pause(False)
        qtbot.waitUntil(lambda: not worker.isRunning(), timeout=10_000)
    finally:
        worker.request_stop()
        worker.wait(2000)


def _wait_until_frozen(worker: SimulationWorker, qtbot) -> object:
    """Wait until no new snapshot is published for 150 ms (gate engaged)."""
    last = worker.take_snapshot()
    stable_since = time.monotonic()
    while time.monotonic() - stable_since < 0.15:
        qtbot.wait(20)
        current = worker.take_snapshot()
        if current is not last:
            last = current
            stable_since = time.monotonic()
    return last


def test_window_run_matches_headless_then_resets(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.dashboard.ui.countSpin.setValue(6)
    window.dashboard.ui.seedSpin.setValue(42)
    window.dashboard.ui.numStepsSpin.setValue(4)

    window.start_run()
    assert window.is_running()
    qtbot.waitUntil(lambda: not window.is_running(), timeout=30_000)

    expected = _headless_result(42, 6, 4)
    assert window.last_result is not None and window.last_result.summary is not None
    assert expected.summary is not None
    assert window.last_result.summary.to_dict() == expected.summary.to_dict()
    assert window.dashboard.ui.progressLabel.text() == f"{expected.summary.moved}/6"
    assert window.dashboard.ui.attemptsLabel.text() == str(expected.summary.total_attempts)

    window.reset_run()
    assert window.dashboard.ui.progressLabel.text() == "—"
    assert not window.is_running()


def test_window_stop_then_close_is_clean(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.dashboard.ui.numStepsSpin.setValue(50)  # long run to stop mid-way

    window.start_run()
    qtbot.waitUntil(lambda: window.dashboard.ui.toolStateLabel.text() != "—", timeout=5000)
    window.stop_run()
    qtbot.waitUntil(lambda: not window.is_running(), timeout=5000)
    assert window.last_result is not None
    assert window.last_result.finish_reason == FinishReason.STOPPED

    started = time.monotonic()
    assert window.close()
    assert time.monotonic() - started < 2.0


def test_window_export_image_writes_png(qtbot, tmp_path: Path) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.wait(100)

    path = window.export_image(tmp_path / "scene.png")

    assert path.exists()
    assert path.stat().st_size > 0


def test_window_accepts_injected_config_and_lists_configs(qtbot) -> None:
    ws = load_workspace("default")
    window = MainWindow(AppConfig(workspace=ws, embryo=load_embryo(), tool=load_tool_head()))
    qtbot.addWidget(window)

    assert window.workspace is ws
    # the Config menu is populated from config/workspace/*.yaml at startup
    labels = [action.text() for action in window.ui.menuConfig.actions()]
    assert "default" in labels


def _write_alt_config(tmp_path: Path) -> None:
    """Stage a config root under ``tmp_path`` with a shrunk workspace ``alt`` config."""
    source_root = Path(__file__).resolve().parents[1] / "config"
    for section in ("workspace", "embryo", "tool_head"):
        (tmp_path / section).mkdir()
        for path in (source_root / section).glob("*.yaml"):
            (tmp_path / section / path.name).write_text(
                path.read_text(encoding="utf-8"), encoding="utf-8"
            )
    default = tmp_path / "workspace" / "default.yaml"
    (tmp_path / "workspace" / "alt.yaml").write_text(
        default.read_text(encoding="utf-8").replace("size: [100, 40, 10]", "size: [80, 30, 8]"),
        encoding="utf-8",
    )


def test_window_apply_config_switches_workspace(qtbot, tmp_path: Path) -> None:
    _write_alt_config(tmp_path)
    window = MainWindow()
    qtbot.addWidget(window)
    original = window.workspace

    assert window.apply_config(load_app_config("alt", config_dir=tmp_path))
    assert window.workspace is not original
    assert list(window.workspace.size) == [80.0, 30.0, 8.0]


def test_window_apply_config_blocked_while_running(qtbot, tmp_path: Path) -> None:
    _write_alt_config(tmp_path)
    window = MainWindow()
    qtbot.addWidget(window)
    window.dashboard.ui.numStepsSpin.setValue(50)

    window.start_run()
    assert window.is_running()

    alt = load_app_config("alt", config_dir=tmp_path)
    assert window.apply_config(alt) is False  # ignored: worker holds the workspace
    assert window.workspace.material == "glass"  # unchanged

    window.stop_run()
    qtbot.waitUntil(lambda: not window.is_running(), timeout=10_000)
