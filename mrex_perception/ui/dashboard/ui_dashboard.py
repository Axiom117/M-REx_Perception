# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_DashboardPanel(object):
    def setupUi(self, DashboardPanel):
        if not DashboardPanel.objectName():
            DashboardPanel.setObjectName(u"DashboardPanel")
        DashboardPanel.resize(300, 760)
        DashboardPanel.setMinimumSize(QSize(280, 0))
        DashboardPanel.setMaximumSize(QSize(340, 16777215))
        self.rootLayout = QVBoxLayout(DashboardPanel)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(8, 8, 4, 8)
        self.runGroup = QGroupBox(DashboardPanel)
        self.runGroup.setObjectName(u"runGroup")
        self.runGrid = QGridLayout(self.runGroup)
        self.runGrid.setObjectName(u"runGrid")
        self.startButton = QPushButton(self.runGroup)
        self.startButton.setObjectName(u"startButton")

        self.runGrid.addWidget(self.startButton, 0, 0, 1, 1)

        self.pauseButton = QPushButton(self.runGroup)
        self.pauseButton.setObjectName(u"pauseButton")

        self.runGrid.addWidget(self.pauseButton, 0, 1, 1, 1)

        self.stepButton = QPushButton(self.runGroup)
        self.stepButton.setObjectName(u"stepButton")

        self.runGrid.addWidget(self.stepButton, 1, 0, 1, 1)

        self.stopButton = QPushButton(self.runGroup)
        self.stopButton.setObjectName(u"stopButton")

        self.runGrid.addWidget(self.stopButton, 1, 1, 1, 1)

        self.resetButton = QPushButton(self.runGroup)
        self.resetButton.setObjectName(u"resetButton")

        self.runGrid.addWidget(self.resetButton, 2, 0, 1, 1)


        self.rootLayout.addWidget(self.runGroup)

        self.sourceGroup = QGroupBox(DashboardPanel)
        self.sourceGroup.setObjectName(u"sourceGroup")
        self.sourceLayout = QVBoxLayout(self.sourceGroup)
        self.sourceLayout.setObjectName(u"sourceLayout")
        self.randomRadio = QRadioButton(self.sourceGroup)
        self.randomRadio.setObjectName(u"randomRadio")
        self.randomRadio.setChecked(True)

        self.sourceLayout.addWidget(self.randomRadio)

        self.imageRadio = QRadioButton(self.sourceGroup)
        self.imageRadio.setObjectName(u"imageRadio")
        self.imageRadio.setEnabled(False)

        self.sourceLayout.addWidget(self.imageRadio)

        self.sourceGrid = QGridLayout()
        self.sourceGrid.setObjectName(u"sourceGrid")
        self.countLabel = QLabel(self.sourceGroup)
        self.countLabel.setObjectName(u"countLabel")

        self.sourceGrid.addWidget(self.countLabel, 0, 0, 1, 1)

        self.countSpin = QSpinBox(self.sourceGroup)
        self.countSpin.setObjectName(u"countSpin")
        self.countSpin.setMinimum(1)
        self.countSpin.setMaximum(200)
        self.countSpin.setValue(6)

        self.sourceGrid.addWidget(self.countSpin, 0, 1, 1, 1)

        self.seedLabel = QLabel(self.sourceGroup)
        self.seedLabel.setObjectName(u"seedLabel")

        self.sourceGrid.addWidget(self.seedLabel, 1, 0, 1, 1)

        self.seedSpin = QSpinBox(self.sourceGroup)
        self.seedSpin.setObjectName(u"seedSpin")
        self.seedSpin.setMaximum(2147483647)
        self.seedSpin.setValue(42)

        self.sourceGrid.addWidget(self.seedSpin, 1, 1, 1, 1)


        self.sourceLayout.addLayout(self.sourceGrid)


        self.rootLayout.addWidget(self.sourceGroup)

        self.paramGroup = QGroupBox(DashboardPanel)
        self.paramGroup.setObjectName(u"paramGroup")
        self.paramGrid = QGridLayout(self.paramGroup)
        self.paramGrid.setObjectName(u"paramGrid")
        self.numStepsLabel = QLabel(self.paramGroup)
        self.numStepsLabel.setObjectName(u"numStepsLabel")

        self.paramGrid.addWidget(self.numStepsLabel, 0, 0, 1, 1)

        self.numStepsSpin = QSpinBox(self.paramGroup)
        self.numStepsSpin.setObjectName(u"numStepsSpin")
        self.numStepsSpin.setMinimum(1)
        self.numStepsSpin.setMaximum(10000)
        self.numStepsSpin.setValue(50)

        self.paramGrid.addWidget(self.numStepsSpin, 0, 1, 1, 1)

        self.targetLabel = QLabel(self.paramGroup)
        self.targetLabel.setObjectName(u"targetLabel")

        self.paramGrid.addWidget(self.targetLabel, 1, 0, 1, 2)

        self.targetLayout = QHBoxLayout()
        self.targetLayout.setObjectName(u"targetLayout")
        self.targetXSpin = QDoubleSpinBox(self.paramGroup)
        self.targetXSpin.setObjectName(u"targetXSpin")
        self.targetXSpin.setDecimals(2)
        self.targetXSpin.setMinimum(-1000.000000000000000)
        self.targetXSpin.setMaximum(1000.000000000000000)
        self.targetXSpin.setValue(50.000000000000000)

        self.targetLayout.addWidget(self.targetXSpin)

        self.targetYSpin = QDoubleSpinBox(self.paramGroup)
        self.targetYSpin.setObjectName(u"targetYSpin")
        self.targetYSpin.setDecimals(2)
        self.targetYSpin.setMinimum(-1000.000000000000000)
        self.targetYSpin.setMaximum(1000.000000000000000)
        self.targetYSpin.setValue(50.000000000000000)

        self.targetLayout.addWidget(self.targetYSpin)

        self.targetZSpin = QDoubleSpinBox(self.paramGroup)
        self.targetZSpin.setObjectName(u"targetZSpin")
        self.targetZSpin.setDecimals(2)
        self.targetZSpin.setMinimum(-1000.000000000000000)
        self.targetZSpin.setMaximum(1000.000000000000000)
        self.targetZSpin.setValue(0.100000000000000)

        self.targetLayout.addWidget(self.targetZSpin)


        self.paramGrid.addLayout(self.targetLayout, 2, 0, 1, 2)


        self.rootLayout.addWidget(self.paramGroup)

        self.telemetryGroup = QGroupBox(DashboardPanel)
        self.telemetryGroup.setObjectName(u"telemetryGroup")
        self.telemetryForm = QFormLayout(self.telemetryGroup)
        self.telemetryForm.setObjectName(u"telemetryForm")
        self.toolStateTitle = QLabel(self.telemetryGroup)
        self.toolStateTitle.setObjectName(u"toolStateTitle")

        self.telemetryForm.setWidget(0, QFormLayout.ItemRole.LabelRole, self.toolStateTitle)

        self.toolStateLabel = QLabel(self.telemetryGroup)
        self.toolStateLabel.setObjectName(u"toolStateLabel")

        self.telemetryForm.setWidget(0, QFormLayout.ItemRole.FieldRole, self.toolStateLabel)

        self.progressTitle = QLabel(self.telemetryGroup)
        self.progressTitle.setObjectName(u"progressTitle")

        self.telemetryForm.setWidget(1, QFormLayout.ItemRole.LabelRole, self.progressTitle)

        self.progressLabel = QLabel(self.telemetryGroup)
        self.progressLabel.setObjectName(u"progressLabel")

        self.telemetryForm.setWidget(1, QFormLayout.ItemRole.FieldRole, self.progressLabel)

        self.attemptsTitle = QLabel(self.telemetryGroup)
        self.attemptsTitle.setObjectName(u"attemptsTitle")

        self.telemetryForm.setWidget(2, QFormLayout.ItemRole.LabelRole, self.attemptsTitle)

        self.attemptsLabel = QLabel(self.telemetryGroup)
        self.attemptsLabel.setObjectName(u"attemptsLabel")

        self.telemetryForm.setWidget(2, QFormLayout.ItemRole.FieldRole, self.attemptsLabel)

        self.successTitle = QLabel(self.telemetryGroup)
        self.successTitle.setObjectName(u"successTitle")

        self.telemetryForm.setWidget(3, QFormLayout.ItemRole.LabelRole, self.successTitle)

        self.successLabel = QLabel(self.telemetryGroup)
        self.successLabel.setObjectName(u"successLabel")

        self.telemetryForm.setWidget(3, QFormLayout.ItemRole.FieldRole, self.successLabel)


        self.rootLayout.addWidget(self.telemetryGroup)

        self.chartGroup = QGroupBox(DashboardPanel)
        self.chartGroup.setObjectName(u"chartGroup")
        self.chartLayout = QVBoxLayout(self.chartGroup)
        self.chartLayout.setSpacing(4)
        self.chartLayout.setObjectName(u"chartLayout")
        self.zPlot = PlotWidget(self.chartGroup)
        self.zPlot.setObjectName(u"zPlot")
        self.zPlot.setMinimumSize(QSize(0, 80))

        self.chartLayout.addWidget(self.zPlot)

        self.yawPlot = PlotWidget(self.chartGroup)
        self.yawPlot.setObjectName(u"yawPlot")
        self.yawPlot.setMinimumSize(QSize(0, 80))

        self.chartLayout.addWidget(self.yawPlot)

        self.distancePlot = PlotWidget(self.chartGroup)
        self.distancePlot.setObjectName(u"distancePlot")
        self.distancePlot.setMinimumSize(QSize(0, 80))

        self.chartLayout.addWidget(self.distancePlot)


        self.rootLayout.addWidget(self.chartGroup)

        self.noteLabel = QLabel(DashboardPanel)
        self.noteLabel.setObjectName(u"noteLabel")
        self.noteLabel.setWordWrap(True)

        self.rootLayout.addWidget(self.noteLabel)

        self.rootSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.rootLayout.addItem(self.rootSpacer)


        self.retranslateUi(DashboardPanel)

        QMetaObject.connectSlotsByName(DashboardPanel)
    # setupUi

    def retranslateUi(self, DashboardPanel):
        self.runGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Control", None))
#if QT_CONFIG(tooltip)
        self.startButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"\u5f00\u59cb\u8fd0\u884c (F5)", None))
#endif // QT_CONFIG(tooltip)
        self.startButton.setText(QCoreApplication.translate("DashboardPanel", u"Start", None))
#if QT_CONFIG(tooltip)
        self.pauseButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"\u6682\u505c / \u7ee7\u7eed (F6)", None))
#endif // QT_CONFIG(tooltip)
        self.pauseButton.setText(QCoreApplication.translate("DashboardPanel", u"Pause", None))
#if QT_CONFIG(tooltip)
        self.stepButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"\u5355\u6b65\uff08\u6682\u505c\u65f6\u53ef\u7528\uff09 (F7)", None))
#endif // QT_CONFIG(tooltip)
        self.stepButton.setText(QCoreApplication.translate("DashboardPanel", u"Step", None))
#if QT_CONFIG(tooltip)
        self.stopButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"\u505c\u6b62 (Shift+F5)", None))
#endif // QT_CONFIG(tooltip)
        self.stopButton.setText(QCoreApplication.translate("DashboardPanel", u"Stop", None))
#if QT_CONFIG(tooltip)
        self.resetButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"\u6e05\u9664\u573a\u666f\u4e0e\u7edf\u8ba1 (Ctrl+R)", None))
#endif // QT_CONFIG(tooltip)
        self.resetButton.setText(QCoreApplication.translate("DashboardPanel", u"Reset", None))
        self.sourceGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Source", None))
        self.randomRadio.setText(QCoreApplication.translate("DashboardPanel", u"Random Arrangement", None))
        self.imageRadio.setText(QCoreApplication.translate("DashboardPanel", u"Image Detection / YOLO (M5)", None))
        self.countLabel.setText(QCoreApplication.translate("DashboardPanel", u"count", None))
        self.seedLabel.setText(QCoreApplication.translate("DashboardPanel", u"seed", None))
#if QT_CONFIG(tooltip)
        self.seedSpin.setToolTip(QCoreApplication.translate("DashboardPanel", u"\u56fa\u5b9a\u79cd\u5b50\u4fbf\u4e8e\u590d\u73b0\uff08\u6bcf\u6b21\u8fd0\u884c\u4f7f\u7528\u540c\u4e00\u5e8f\u5217\uff09", None))
#endif // QT_CONFIG(tooltip)
        self.paramGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Parameters", None))
        self.numStepsLabel.setText(QCoreApplication.translate("DashboardPanel", u"num_steps", None))
        self.targetLabel.setText(QCoreApplication.translate("DashboardPanel", u"target point", None))
        self.telemetryGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Telemetry", None))
        self.toolStateTitle.setText(QCoreApplication.translate("DashboardPanel", u"Tool state", None))
        self.toolStateLabel.setText(QCoreApplication.translate("DashboardPanel", u"\u2014", None))
        self.progressTitle.setText(QCoreApplication.translate("DashboardPanel", u"Progress", None))
        self.progressLabel.setText(QCoreApplication.translate("DashboardPanel", u"\u2014", None))
        self.attemptsTitle.setText(QCoreApplication.translate("DashboardPanel", u"Attempts", None))
        self.attemptsLabel.setText(QCoreApplication.translate("DashboardPanel", u"\u2014", None))
        self.successTitle.setText(QCoreApplication.translate("DashboardPanel", u"Success", None))
        self.successLabel.setText(QCoreApplication.translate("DashboardPanel", u"\u2014", None))
        self.chartGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Charts", None))
        self.noteLabel.setStyleSheet(QCoreApplication.translate("DashboardPanel", u"color: #8b94a3;", None))
        self.noteLabel.setText(QCoreApplication.translate("DashboardPanel", u"\u4eff\u771f\u6a21\u5f0f\uff08Random\uff09\uff1bYOLO\uff08M5\uff09\u4e0e\u786c\u4ef6\uff08M6\uff09\u540e\u7eed\u63a5\u5165\u3002", None))
        pass
    # retranslateUi

