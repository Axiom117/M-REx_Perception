"""Dashboard component: Designer form (``dashboard.ui``), uic output, wrapper.

The public import path ``mrex_perception.ui.dashboard`` is kept stable by
re-exporting the panel class here.
"""

from .dashboard import DashboardPanel

__all__ = ["DashboardPanel"]
