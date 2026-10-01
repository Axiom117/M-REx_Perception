"""Application entry point: creates the QApplication and the main window."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from mrex_perception import __version__
from mrex_perception.ui.main_window import MainWindow
from mrex_perception.ui.theme import apply_theme


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="mrex", description="M-REx Perception GUI")
    parser.add_argument("--version", action="version", version=f"mrex {__version__}")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="show the window and quit automatically (startup smoke test)",
    )
    parser.add_argument(
        "--smoke-delay",
        type=int,
        default=3000,
        metavar="MS",
        help="auto-quit delay in milliseconds for --smoke (default: 3000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the GUI application and return the process exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    app = QApplication(sys.argv)
    app.setApplicationName("M-REx Perception")
    app.setApplicationVersion(__version__)
    apply_theme(app)

    window = MainWindow()
    window.show()

    if args.smoke:
        print(f"[smoke] window shown; auto-quit in {args.smoke_delay} ms")
        QTimer.singleShot(args.smoke_delay, app.quit)

    exit_code = int(app.exec())

    if args.smoke:
        print(f"[smoke] exited normally (code {exit_code})")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
