"""Dark theme for the application (Fusion base style + QSS tweaks)."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

_STYLESHEET = """
QWidget {
    background-color: #23262e;
    color: #d8dce3;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #3a3f4b;
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #9aa4b2;
}
QPushButton {
    background: #2f3542;
    border: 1px solid #454c5c;
    border-radius: 4px;
    padding: 5px 14px;
}
QPushButton:hover { background: #3a4150; }
QPushButton:pressed { background: #262b36; }
QPushButton:disabled { color: #6b7280; background: #262a33; border-color: #333844; }
QRadioButton, QCheckBox { spacing: 6px; }
QRadioButton:disabled, QCheckBox:disabled { color: #6b7280; }
QSpinBox, QDoubleSpinBox, QLineEdit {
    background: #1c1f26;
    border: 1px solid #3a3f4b;
    border-radius: 4px;
    padding: 3px 6px;
}
QSpinBox:disabled, QDoubleSpinBox:disabled, QLineEdit:disabled { color: #6b7280; }
QStatusBar { background: #1b1d22; color: #9aa4b2; }
QStatusBar::item { border: none; }
QMenuBar { background: #1b1d22; }
QMenuBar::item { padding: 4px 10px; background: transparent; }
QMenuBar::item:selected { background: #2f3542; }
QMenu { background: #23262e; border: 1px solid #3a3f4b; }
QMenu::item:selected { background: #2f3542; }
QMenu::item:disabled { color: #6b7280; }
"""


def apply_theme(app: QApplication) -> None:
    """Apply the dark Fusion theme to the application."""
    app.setStyle("Fusion")
    app.setStyleSheet(_STYLESHEET)
