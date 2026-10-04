"""Main window component: Designer form (``main_window.ui``), uic output, wiring.

The public import path ``mrex_perception.ui.main_window`` is kept stable by
re-exporting the window class here.
"""

from .main_window import MainWindow

__all__ = ["MainWindow"]
