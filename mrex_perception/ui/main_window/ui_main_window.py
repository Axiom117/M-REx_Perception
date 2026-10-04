# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QMenu, QMenuBar, QSizePolicy, QStatusBar,
    QWidget)

from mrex_perception.ui.dashboard import DashboardPanel
from mrex_perception.ui.viewport import MultiViewPanel

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1500, 900)
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionStart = QAction(MainWindow)
        self.actionStart.setObjectName(u"actionStart")
        self.actionStart.setEnabled(False)
        self.actionPause = QAction(MainWindow)
        self.actionPause.setObjectName(u"actionPause")
        self.actionPause.setEnabled(False)
        self.actionStep = QAction(MainWindow)
        self.actionStep.setObjectName(u"actionStep")
        self.actionStep.setEnabled(False)
        self.actionStop = QAction(MainWindow)
        self.actionStop.setObjectName(u"actionStop")
        self.actionStop.setEnabled(False)
        self.actionReset = QAction(MainWindow)
        self.actionReset.setObjectName(u"actionReset")
        self.actionReset.setEnabled(False)
        self.actionFitAll = QAction(MainWindow)
        self.actionFitAll.setObjectName(u"actionFitAll")
        self.actionResetView = QAction(MainWindow)
        self.actionResetView.setObjectName(u"actionResetView")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralLayout = QHBoxLayout(self.centralwidget)
        self.centralLayout.setSpacing(8)
        self.centralLayout.setObjectName(u"centralLayout")
        self.centralLayout.setContentsMargins(4, 4, 4, 4)
        self.dashboard = DashboardPanel(self.centralwidget)
        self.dashboard.setObjectName(u"dashboard")

        self.centralLayout.addWidget(self.dashboard)

        self.viewports = MultiViewPanel(self.centralwidget)
        self.viewports.setObjectName(u"viewports")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.viewports.sizePolicy().hasHeightForWidth())
        self.viewports.setSizePolicy(sizePolicy)

        self.centralLayout.addWidget(self.viewports)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1500, 24))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuRun = QMenu(self.menubar)
        self.menuRun.setObjectName(u"menuRun")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.versionLabel = QLabel(self.statusbar)
        self.versionLabel.setObjectName(u"versionLabel")
        self.versionLabel.setText(u"")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuRun.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionQuit)
        self.menuRun.addAction(self.actionStart)
        self.menuRun.addAction(self.actionPause)
        self.menuRun.addAction(self.actionStep)
        self.menuRun.addAction(self.actionStop)
        self.menuRun.addAction(self.actionReset)
        self.menuView.addAction(self.actionFitAll)
        self.menuView.addAction(self.actionResetView)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"M-REx Perception", None))
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"\u9000\u51fa", None))
#if QT_CONFIG(shortcut)
        self.actionQuit.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.actionStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
#if QT_CONFIG(statustip)
        self.actionStart.setStatusTip(QCoreApplication.translate("MainWindow", u"M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(statustip)
        self.actionPause.setText(QCoreApplication.translate("MainWindow", u"Pause", None))
#if QT_CONFIG(statustip)
        self.actionPause.setStatusTip(QCoreApplication.translate("MainWindow", u"M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(statustip)
        self.actionStep.setText(QCoreApplication.translate("MainWindow", u"Step", None))
#if QT_CONFIG(statustip)
        self.actionStep.setStatusTip(QCoreApplication.translate("MainWindow", u"M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(statustip)
        self.actionStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
#if QT_CONFIG(statustip)
        self.actionStop.setStatusTip(QCoreApplication.translate("MainWindow", u"M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(statustip)
        self.actionReset.setText(QCoreApplication.translate("MainWindow", u"Reset", None))
#if QT_CONFIG(statustip)
        self.actionReset.setStatusTip(QCoreApplication.translate("MainWindow", u"M4 \u63a5\u5165\u4eff\u771f\u5f15\u64ce\u540e\u542f\u7528", None))
#endif // QT_CONFIG(statustip)
        self.actionFitAll.setText(QCoreApplication.translate("MainWindow", u"Fit All", None))
#if QT_CONFIG(shortcut)
        self.actionFitAll.setShortcut(QCoreApplication.translate("MainWindow", u"F", None))
#endif // QT_CONFIG(shortcut)
        self.actionResetView.setText(QCoreApplication.translate("MainWindow", u"\u590d\u4f4d\u89c6\u89d2", None))
#if QT_CONFIG(shortcut)
        self.actionResetView.setShortcut(QCoreApplication.translate("MainWindow", u"0", None))
#endif // QT_CONFIG(shortcut)
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"\u5173\u4e8e", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File(&F)", None))
        self.menuRun.setTitle(QCoreApplication.translate("MainWindow", u"Run(&R)", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View(&V)", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help(&H)", None))
    # retranslateUi

