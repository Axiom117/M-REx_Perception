"""M0 smoke tests: package and key modules must be importable."""

import mrex


def test_version_present() -> None:
    assert mrex.__version__


def test_ui_modules_importable() -> None:
    from mrex.ui.main_window import MainWindow  # noqa: F401
    from mrex.ui.viewport import MultiViewPanel  # noqa: F401


def test_main_entrypoint_callable() -> None:
    from mrex.main import main

    assert callable(main)
