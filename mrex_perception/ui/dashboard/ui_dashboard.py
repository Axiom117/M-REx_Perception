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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

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
        self.startButton.setEnabled(False)

        self.runGrid.addWidget(self.startButton, 0, 0, 1, 1)

        self.pauseButton = QPushButton(self.runGroup)
        self.pauseButton.setObjectName(u"pauseButton")
        self.pauseButton.setEnabled(False)

        self.runGrid.addWidget(self.pauseButton, 0, 1, 1, 1)

        self.stepButton = QPushButton(self.runGroup)
        self.stepButton.setObjectName(u"stepButton")
        self.stepButton.setEnabled(False)

        self.runGrid.addWidget(self.stepButton, 1, 0, 1, 1)

        self.stopButton = QPushButton(self.runGroup)
        self.stopButton.setObjectName(u"stopButton")
        self.stopButton.setEnabled(False)

        self.runGrid.addWidget(self.stopButton, 1, 1, 1, 1)

        self.resetButton = QPushButton(self.runGroup)
        self.resetButton.setObjectName(u"resetButton")
        self.resetButton.setEnabled(False)

        self.runGrid.addWidget(self.resetButton, 2, 0, 1, 1)


        self.rootLayout.addWidget(self.runGroup)

        self.sourceGroup = QGroupBox(DashboardPanel)
        self.sourceGroup.setObjectName(u"sourceGroup")
        self.sourceLayout = QVBoxLayout(self.sourceGroup)
        self.sourceLayout.setObjectName(u"sourceLayout")
        self.randomRadio = QRadioButton(self.sourceGroup)
        self.randomRadio.setObjectName(u"randomRadio")
        self.randomRadio.setEnabled(False)
        self.randomRadio.setChecked(True)

        self.sourceLayout.addWidget(self.randomRadio)

        self.imageRadio = QRadioButton(self.sourceGroup)
        self.imageRadio.setObjectName(u"imageRadio")
        self.imageRadio.setEnabled(False)

        self.sourceLayout.addWidget(self.imageRadio)


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
        self.numStepsSpin.setEnabled(False)
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
        self.targetXSpin.setEnabled(False)
        self.targetXSpin.setDecimals(2)
        self.targetXSpin.setMinimum(-1000.000000000000000)
        self.targetXSpin.setMaximum(1000.000000000000000)
        self.targetXSpin.setValue(50.000000000000000)

        self.targetLayout.addWidget(self.targetXSpin)

        self.targetYSpin = QDoubleSpinBox(self.paramGroup)
        self.targetYSpin.setObjectName(u"targetYSpin")
        self.targetYSpin.setEnabled(False)
        self.targetYSpin.setDecimals(2)
        self.targetYSpin.setMinimum(-1000.000000000000000)
        self.targetYSpin.setMaximum(1000.000000000000000)
        self.targetYSpin.setValue(50.000000000000000)

        self.targetLayout.addWidget(self.targetYSpin)

        self.targetZSpin = QDoubleSpinBox(self.paramGroup)
        self.targetZSpin.setObjectName(u"targetZSpin")
        self.targetZSpin.setEnabled(False)
        self.targetZSpin.setDecimals(2)
        self.targetZSpin.setMinimum(-1000.000000000000000)
        self.targetZSpin.setMaximum(1000.000000000000000)
        self.targetZSpin.setValue(0.100000000000000)

        self.targetLayout.addWidget(self.targetZSpin)


        self.paramGrid.addLayout(self.targetLayout, 2, 0, 1, 2)


        self.rootLayout.addWidget(self.paramGroup)

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
        self.startButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"M3/M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(tooltip)
        self.startButton.setText(QCoreApplication.translate("DashboardPanel", u"Start", None))
#if QT_CONFIG(tooltip)
        self.pauseButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"M3/M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(tooltip)
        self.pauseButton.setText(QCoreApplication.translate("DashboardPanel", u"Pause", None))
#if QT_CONFIG(tooltip)
        self.stepButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"M3/M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(tooltip)
        self.stepButton.setText(QCoreApplication.translate("DashboardPanel", u"Step", None))
#if QT_CONFIG(tooltip)
        self.stopButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"M3/M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(tooltip)
        self.stopButton.setText(QCoreApplication.translate("DashboardPanel", u"Stop", None))
#if QT_CONFIG(tooltip)
        self.resetButton.setToolTip(QCoreApplication.translate("DashboardPanel", u"M3/M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(tooltip)
        self.resetButton.setText(QCoreApplication.translate("DashboardPanel", u"Reset", None))
        self.sourceGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Source", None))
        self.randomRadio.setText(QCoreApplication.translate("DashboardPanel", u"Random Arrangement (M1)", None))
        self.imageRadio.setText(QCoreApplication.translate("DashboardPanel", u"Image Detection / YOLO (M5)", None))
        self.paramGroup.setTitle(QCoreApplication.translate("DashboardPanel", u"Parameters", None))
        self.numStepsLabel.setText(QCoreApplication.translate("DashboardPanel", u"num_steps", None))
        self.targetLabel.setText(QCoreApplication.translate("DashboardPanel", u"target point", None))
        self.noteLabel.setStyleSheet(QCoreApplication.translate("DashboardPanel", u"color: #8b94a3;", None))
        self.noteLabel.setText(QCoreApplication.translate("DashboardPanel", u"M0 \u5360\u4f4d\uff1a\u63a7\u4ef6\u5c06\u5728 M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce", None))
        pass
    # retranslateUi

