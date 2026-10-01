"""Dashboard panel: run controls / embryo source / parameters.

M0: layout and placeholder widgets only. All controls are disabled until the
simulation engine (M3) and the UI wiring (M4) land.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class DashboardPanel(QWidget):
    """Left-hand control panel (placeholder for M4)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(340)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 4, 8)
        root.setSpacing(10)

        root.addWidget(self._run_group())
        root.addWidget(self._source_group())
        root.addWidget(self._param_group())

        note = QLabel("M0 占位：控件将在 M4 接入仿真引擎")
        note.setWordWrap(True)
        note.setStyleSheet("color: #8b94a3;")
        root.addWidget(note)
        root.addStretch(1)

    # -- groups ---------------------------------------------------------------

    @staticmethod
    def _run_group() -> QGroupBox:
        box = QGroupBox("运行控制")
        grid = QGridLayout(box)
        for index, text in enumerate(("Start", "Pause", "Step", "Stop", "Reset")):
            button = QPushButton(text)
            button.setEnabled(False)
            button.setToolTip("M3/M4 接入仿真引擎后启用")
            grid.addWidget(button, index // 2, index % 2)
        return box

    @staticmethod
    def _source_group() -> QGroupBox:
        box = QGroupBox("胚胎来源")
        layout = QVBoxLayout(box)
        random_radio = QRadioButton("随机布置（M1）")
        random_radio.setChecked(True)
        random_radio.setEnabled(False)
        image_radio = QRadioButton("图像检测 / YOLO（M5）")
        image_radio.setEnabled(False)
        layout.addWidget(random_radio)
        layout.addWidget(image_radio)
        return box

    @staticmethod
    def _param_group() -> QGroupBox:
        box = QGroupBox("参数")
        grid = QGridLayout(box)

        grid.addWidget(QLabel("num_steps"), 0, 0)
        num_steps = QSpinBox()
        num_steps.setRange(1, 10000)
        num_steps.setValue(50)
        num_steps.setEnabled(False)
        grid.addWidget(num_steps, 0, 1)

        grid.addWidget(QLabel("target point"), 1, 0, 1, 2)
        target_row = QHBoxLayout()
        for value in (50.0, 50.0, 0.1):
            spin = QDoubleSpinBox()
            spin.setRange(-1000.0, 1000.0)
            spin.setDecimals(2)
            spin.setValue(value)
            spin.setEnabled(False)
            target_row.addWidget(spin)
        grid.addLayout(target_row, 2, 0, 1, 2)

        return box
