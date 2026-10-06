"""Application entry point: creates the QApplication and the main window."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from mrex_perception import __version__
from mrex_perception.config.app import load_app_config
from mrex_perception.ui.main_window import MainWindow
from mrex_perception.ui.theme import apply_theme


# Parse arguments first so that --version/--help work without starting the GUI.
def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="mrex", description="M-REx Perception GUI")

    # Show version information and exit 
    parser.add_argument("--version", action="version", version=f"mrex {__version__}")
    parser.add_argument(
        "--config", default="default", help="workspace config name (default: %(default)s)"
    )
    return parser.parse_args(argv)

# Entry point for the application with optional command-line arguments
def main(argv: list[str] | None = None) -> int:
    """Run the GUI application and return the process exit code."""
    # Skip the 0-th argument (script name) when parsing arguments.
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    # Initialize the Qt application.
    app = QApplication(sys.argv)
    app.setApplicationName("M-REx Perception")
    app.setApplicationVersion(__version__)
    apply_theme(app)

    # Instantiate and show the main window with the loaded app config
    window = MainWindow(load_app_config(args.config))
    window.show()

    # Enter the Qt main event loop.
    return int(app.exec())

# Only run the application if this module is executed as the main script.
if __name__ == "__main__":
    raise SystemExit(main())
