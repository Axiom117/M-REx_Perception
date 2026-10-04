"""M0 smoke tests: package and key modules must be importable."""

import mrex_perception


def test_package_version_and_entrypoint() -> None:
    from mrex_perception.main import main

    assert mrex_perception.__version__
    assert callable(main)


def test_ui_modules_importable() -> None:
    from mrex_perception.ui.main_window import MainWindow  # noqa: F401
    from mrex_perception.ui.viewport import MultiViewPanel  # noqa: F401
