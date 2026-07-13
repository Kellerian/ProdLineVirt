# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Main.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QMainWindow,
    QMenu, QMenuBar, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 546)
        MainWindow.setStyleSheet(u"QScrollBar {\n"
"	background: none;\n"
"	border: 1px;\n"
"	margin: 1;\n"
"	padding: 1;\n"
"	width: 15px;\n"
"}\n"
"\n"
"QScrollBar:handle {\n"
"	border: 1px solid #FF17365D;\n"
"	background: #226091;\n"
"	border-radius: 3px;\n"
"	min-height: 45px;\n"
"	min-width: 15px;\n"
"}\n"
"\n"
"QScrollBar:sub-line {\n"
"	background: none;\n"
"	border: none;\n"
"	height: 0px;\n"
"	padding: 0;\n"
"	width: 0px;\n"
"}\n"
"\n"
"QScrollBar:add-line {\n"
"	background:  none;\n"
"	border: none;\n"
"	height: 0px;	\n"
"	padding: 0;\n"
"	width: 0px;\n"
"}\n"
"\n"
"QMenuBar {\n"
"	background-color: #ffffff;\n"
"	color: #17365D;\n"
"}\n"
"\n"
"QMenuBar::item {\n"
"	background-color: transparent;\n"
"	color: #17365D;\n"
"	padding: 2px 8px;\n"
"}\n"
"\n"
"QMenuBar::item:selected {\n"
"	background-color: #226091;\n"
"	color: #f0b321;\n"
"}\n"
"\n"
"QMenuBar::item:pressed {\n"
"	background-color: #226091;\n"
"	color: #f0b321;\n"
"}\n"
"\n"
"QMenu {\n"
"	background-color: #f5f5f5;\n"
"	color: #17365D;\n"
"	border: 1px solid #17365D;\n"
"}"
                        "\n"
"\n"
"QMenu::separator {\n"
"	height: 1px;\n"
"	background: #17365D;\n"
"	margin: 4px 8px;\n"
"}\n"
"\n"
"QMenu::item {\n"
"	background-color: transparent;\n"
"	color: #17365D;\n"
"	padding: 4px 24px 4px 8px;\n"
"}\n"
"\n"
"QMenu::item:selected {\n"
"	background-color: #226091;\n"
"	color: #f0b321;\n"
"}")
        self.acAddCamera = QAction(MainWindow)
        self.acAddCamera.setObjectName(u"acAddCamera")
        self.acAddPrinter = QAction(MainWindow)
        self.acAddPrinter.setObjectName(u"acAddPrinter")
        self.acAddScanner = QAction(MainWindow)
        self.acAddScanner.setObjectName(u"acAddScanner")
        self.acAddTransporter = QAction(MainWindow)
        self.acAddTransporter.setObjectName(u"acAddTransporter")
        self.acOpen = QAction(MainWindow)
        self.acOpen.setObjectName(u"acOpen")
        self.acSaveAs = QAction(MainWindow)
        self.acSaveAs.setObjectName(u"acSaveAs")
        self.acSave = QAction(MainWindow)
        self.acSave.setObjectName(u"acSave")
        self.acClose = QAction(MainWindow)
        self.acClose.setObjectName(u"acClose")
        self.acAddGenerator = QAction(MainWindow)
        self.acAddGenerator.setObjectName(u"acAddGenerator")
        self.acControlStartAll = QAction(MainWindow)
        self.acControlStartAll.setObjectName(u"acControlStartAll")
        self.acControlStartPrinters = QAction(MainWindow)
        self.acControlStartPrinters.setObjectName(u"acControlStartPrinters")
        self.acControlStartCameras = QAction(MainWindow)
        self.acControlStartCameras.setObjectName(u"acControlStartCameras")
        self.acControlStartScanners = QAction(MainWindow)
        self.acControlStartScanners.setObjectName(u"acControlStartScanners")
        self.acControlStartTransporters = QAction(MainWindow)
        self.acControlStartTransporters.setObjectName(u"acControlStartTransporters")
        self.acControlStartGenerators = QAction(MainWindow)
        self.acControlStartGenerators.setObjectName(u"acControlStartGenerators")
        self.acControlStopAll = QAction(MainWindow)
        self.acControlStopAll.setObjectName(u"acControlStopAll")
        self.acControlStopPrinters = QAction(MainWindow)
        self.acControlStopPrinters.setObjectName(u"acControlStopPrinters")
        self.acControlStopCameras = QAction(MainWindow)
        self.acControlStopCameras.setObjectName(u"acControlStopCameras")
        self.acControlStopScanners = QAction(MainWindow)
        self.acControlStopScanners.setObjectName(u"acControlStopScanners")
        self.acControlStopTransporters = QAction(MainWindow)
        self.acControlStopTransporters.setObjectName(u"acControlStopTransporters")
        self.acControlStopGenerators = QAction(MainWindow)
        self.acControlStopGenerators.setObjectName(u"acControlStopGenerators")
        self.acControlClearAll = QAction(MainWindow)
        self.acControlClearAll.setObjectName(u"acControlClearAll")
        self.acControlClearPrinters = QAction(MainWindow)
        self.acControlClearPrinters.setObjectName(u"acControlClearPrinters")
        self.acControlClearCameras = QAction(MainWindow)
        self.acControlClearCameras.setObjectName(u"acControlClearCameras")
        self.acControlClearScanners = QAction(MainWindow)
        self.acControlClearScanners.setObjectName(u"acControlClearScanners")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self.scrollArea_2 = QScrollArea(self.centralwidget)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setMinimumSize(QSize(290, 0))
        self.scrollArea_2.setMaximumSize(QSize(290, 16777215))
        self.scrollArea_2.setFrameShadow(QFrame.Plain)
        self.scrollArea_2.setWidgetResizable(True)
        self.scaTransporters = QWidget()
        self.scaTransporters.setObjectName(u"scaTransporters")
        self.scaTransporters.setGeometry(QRect(0, 0, 288, 520))
        self.scaTransporters.setMinimumSize(QSize(280, 0))
        self.scaTransporters.setMaximumSize(QSize(290, 16777215))
        self.verticalLayout = QVBoxLayout(self.scaTransporters)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.transporters_layout = QVBoxLayout()
        self.transporters_layout.setSpacing(1)
        self.transporters_layout.setObjectName(u"transporters_layout")

        self.verticalLayout.addLayout(self.transporters_layout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.verticalLayout.setStretch(1, 1)
        self.scrollArea_2.setWidget(self.scaTransporters)

        self.horizontalLayout.addWidget(self.scrollArea_2)

        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFrameShadow(QFrame.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scaDevices = QWidget()
        self.scaDevices.setObjectName(u"scaDevices")
        self.scaDevices.setGeometry(QRect(0, 0, 505, 520))
        self.scrollArea.setWidget(self.scaDevices)

        self.horizontalLayout.addWidget(self.scrollArea)

        self.horizontalLayout.setStretch(1, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 800, 22))
        self.menu = QMenu(self.menuBar)
        self.menu.setObjectName(u"menu")
        self.menu_2 = QMenu(self.menuBar)
        self.menu_2.setObjectName(u"menu_2")
        self.menuControl = QMenu(self.menuBar)
        self.menuControl.setObjectName(u"menuControl")
        self.menuControlStart = QMenu(self.menuControl)
        self.menuControlStart.setObjectName(u"menuControlStart")
        self.menuControlStop = QMenu(self.menuControl)
        self.menuControlStop.setObjectName(u"menuControlStop")
        self.menuControlClear = QMenu(self.menuControl)
        self.menuControlClear.setObjectName(u"menuControlClear")
        MainWindow.setMenuBar(self.menuBar)

        self.menuBar.addAction(self.menu_2.menuAction())
        self.menuBar.addAction(self.menu.menuAction())
        self.menuBar.addAction(self.menuControl.menuAction())
        self.menu.addAction(self.acAddCamera)
        self.menu.addAction(self.acAddPrinter)
        self.menu.addAction(self.acAddScanner)
        self.menu.addSeparator()
        self.menu.addAction(self.acAddTransporter)
        self.menu.addSeparator()
        self.menu.addAction(self.acAddGenerator)
        self.menu_2.addAction(self.acOpen)
        self.menu_2.addAction(self.acSaveAs)
        self.menu_2.addAction(self.acSave)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.acClose)
        self.menuControl.addAction(self.menuControlStart.menuAction())
        self.menuControl.addAction(self.menuControlStop.menuAction())
        self.menuControl.addAction(self.menuControlClear.menuAction())
        self.menuControlStart.addAction(self.acControlStartAll)
        self.menuControlStart.addAction(self.acControlStartPrinters)
        self.menuControlStart.addAction(self.acControlStartCameras)
        self.menuControlStart.addAction(self.acControlStartScanners)
        self.menuControlStart.addSeparator()
        self.menuControlStart.addAction(self.acControlStartTransporters)
        self.menuControlStart.addAction(self.acControlStartGenerators)
        self.menuControlStop.addAction(self.acControlStopAll)
        self.menuControlStop.addAction(self.acControlStopPrinters)
        self.menuControlStop.addAction(self.acControlStopCameras)
        self.menuControlStop.addAction(self.acControlStopScanners)
        self.menuControlStop.addSeparator()
        self.menuControlStop.addAction(self.acControlStopTransporters)
        self.menuControlStop.addAction(self.acControlStopGenerators)
        self.menuControlClear.addAction(self.acControlClearAll)
        self.menuControlClear.addAction(self.acControlClearPrinters)
        self.menuControlClear.addAction(self.acControlClearCameras)
        self.menuControlClear.addAction(self.acControlClearScanners)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u042d\u043c\u0443\u043b\u044f\u0442\u043e\u0440 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u044f \u043b\u0438\u043d\u0438\u0438", None))
        self.acAddCamera.setText(QCoreApplication.translate("MainWindow", u"\u041a\u0430\u043c\u0435\u0440\u0430", None))
        self.acAddPrinter.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u043d\u0442\u0435\u0440", None))
        self.acAddScanner.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u043d\u0435\u0440", None))
        self.acAddTransporter.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0435\u0440\u0435\u0432\u043e\u0437\u0447\u0438\u043a", None))
        self.acOpen.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0442\u043a\u0440\u044b\u0442\u044c...", None))
        self.acSaveAs.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043a\u0430\u043a...", None))
        self.acSave.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", None))
        self.acClose.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043a\u0440\u044b\u0442\u044c", None))
        self.acAddGenerator.setText(QCoreApplication.translate("MainWindow", u"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440", None))
        self.acControlStartAll.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0441\u0451", None))
        self.acControlStartPrinters.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u043d\u0442\u0435\u0440\u044b", None))
        self.acControlStartCameras.setText(QCoreApplication.translate("MainWindow", u"\u041a\u0430\u043c\u0435\u0440\u044b", None))
        self.acControlStartScanners.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u043d\u0435\u0440\u044b", None))
        self.acControlStartTransporters.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0435\u0440\u0435\u0432\u043e\u0437\u0447\u0438\u043a\u0438", None))
        self.acControlStartGenerators.setText(QCoreApplication.translate("MainWindow", u"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440\u044b", None))
        self.acControlStopAll.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0441\u0451", None))
        self.acControlStopPrinters.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u043d\u0442\u0435\u0440\u044b", None))
        self.acControlStopCameras.setText(QCoreApplication.translate("MainWindow", u"\u041a\u0430\u043c\u0435\u0440\u044b", None))
        self.acControlStopScanners.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u043d\u0435\u0440\u044b", None))
        self.acControlStopTransporters.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0435\u0440\u0435\u0432\u043e\u0437\u0447\u0438\u043a\u0438", None))
        self.acControlStopGenerators.setText(QCoreApplication.translate("MainWindow", u"\u0413\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440\u044b", None))
        self.acControlClearAll.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0441\u0451", None))
        self.acControlClearPrinters.setText(QCoreApplication.translate("MainWindow", u"\u041f\u0440\u0438\u043d\u0442\u0435\u0440\u044b", None))
        self.acControlClearCameras.setText(QCoreApplication.translate("MainWindow", u"\u041a\u0430\u043c\u0435\u0440\u044b", None))
        self.acControlClearScanners.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043a\u0430\u043d\u0435\u0440\u044b", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c", None))
        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"\u0424\u0430\u0439\u043b", None))
        self.menuControl.setTitle(QCoreApplication.translate("MainWindow", u"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435", None))
        self.menuControlStart.setTitle(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c", None))
        self.menuControlStop.setTitle(QCoreApplication.translate("MainWindow", u"\u041e\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u044c", None))
        self.menuControlClear.setTitle(QCoreApplication.translate("MainWindow", u"\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c \u0434\u0430\u043d\u043d\u044b\u0435", None))
    # retranslateUi

