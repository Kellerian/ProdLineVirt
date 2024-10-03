# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Camera.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox,
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListView, QPushButton, QSizePolicy, QSpinBox,
    QTabWidget, QToolButton, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(260, 250)
        Form.setMinimumSize(QSize(260, 250))
        Form.setMaximumSize(QSize(260, 16777215))
        Form.setStyleSheet(u"QToolButton, QPushButton {\n"
"    qproperty-alignment: AlignCenter;\n"
"	border: 1px solid #FF17365D;\n"
"    border-radius: 3px;\n"
"	background-color: #226091;\n"
"	padding: 3px;\n"
"	color: #FFFFFF;\n"
"	font: bold 12pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QCheckBox {\n"
"	font: bold 10pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QLineEdit {\n"
"	font: 10pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QLabel {\n"
"	font: bold 10pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QPushButton:hover,\n"
"QToolButton:hover {\n"
"	color: #f0b321;\n"
"}\n"
"\n"
"QListView {\n"
"	font: 8pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QPushButton:pressed,\n"
"QPushButton:checked,\n"
"QToolButton:pressed,\n"
"QToolButtont:checked {\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
"	border: 2px solid #f0b321;\n"
"}\n"
"\n"
"QSpinBox {\n"
"    qproperty-alignment: AlignCenter;\n"
"	border: 1px solid #FF17365D;\n"
"	color: #f0b321;\n"
"	background-color: #226091;\n"
"	border-radius: 3px;\n"
"	selection-background-color:#19466a;\n"
"	selection-"
                        "color: #f0b321;\n"
"	font: bold 10pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QSpinBox::up-button { subcontrol-origin: content;  subcontrol-position: right;  width:20px; height: 20px; }\n"
"QSpinBox::down-button {subcontrol-origin: content; subcontrol-position: left;  width:20px; height: 20px; }\n"
"\n"
"QComboBox {\n"
"    border: 1px solid #17365D;\n"
"    border-radius: 3px;\n"
"	font: bold 10pt \"DejaVu Sans Mono\";\n"
"	color: #f0b321;\n"
"    background-color: #226091;\n"
"	padding: 5px;\n"
"}\n"
"\n"
"QComboBox:!editable:on {\n"
"    color: #f0b321;\n"
"	background-color: #19466a;\n"
"	border: 1px solid #f0b321;\n"
"}\n"
"\n"
"QComboBox:on {\n"
"    padding-top: 3px;\n"
"    padding-left: 4px;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    subcontrol-origin: padding;\n"
"    subcontrol-position: right;\n"
"    width: 30px;\n"
"	background-color: #19466a;\n"
"    border-left-width: 1px;\n"
"    border-left-color: #17365D;\n"
"    border-left-style: solid;\n"
"    border-top-right-radius: 5px;\n"
"    border-b"
                        "ottom-right-radius: 5px;\n"
"}\n"
"\n"
"QComboBox::down-arrow:on {\n"
"    top: 1px;\n"
"    left: 1px;\n"
"}\n"
"\n"
"QComboBox QListView {\n"
"    selection-background-color: #f0b321;\n"
"	selection-color: #19466a;\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
"	border: 2px solid #f0b321;\n"
"}\n"
"\n"
"QComboBox QToolTip {\n"
"    font: bold 10pt \"DejaVu Sans Mono\";\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
"	border: 2px solid #f0b321;\n"
"    border-radius: 3px;\n"
"}\n"
"\n"
"QComboBox#cbxProduct QAbstractItemView {\n"
"	min-width: 800px;\n"
"}\n"
"\n"
"QScrollBar {\n"
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
"QScrollBar:add-lin"
                        "e {\n"
"	background:  none;\n"
"	border: none;\n"
"	height: 0px;	\n"
"	padding: 0;\n"
"	width: 0px;\n"
"}\n"
"\n"
"QTabWidget::pane {\n"
"    border-top: 1px solid #C2C7CB;\n"
"}\n"
"\n"
"QTabWidget::tab-bar {\n"
"    left: 3px;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,  stop: 0 #E1E1E1, stop: 0.4 #DDDDDD, stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);\n"
"    border: 1px solid #C4C4C3;\n"
"    border-bottom-color: #C2C7CB;\n"
"    border-top-left-radius: 2px;\n"
"    border-top-right-radius: 2px;\n"
"    min-width: 28ex;\n"
"    padding: 1px;\n"
"	color: #17365D;\n"
"	font: 8pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QTabBar::tab:selected, QTabBar::tab:hover {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #fafafa, stop: 0.4 #f4f4f4, stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    border-color: #9B9B9B;\n"
"    border-bottom-color: #C2C7CB;\n"
"	font: bold 8pt \"DejaVu Sans Mono\"\n"
"}\n"
"\n"
"QTabBar::ta"
                        "b:!selected {\n"
"    margin-top: 1px;\n"
"	font: 8pt \"DejaVu Sans Mono\"\n"
"}")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leName = QLineEdit(Form)
        self.leName.setObjectName(u"leName")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy)
        font = QFont()
        font.setFamilies([u"DejaVu Sans Mono"])
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        self.leName.setFont(font)
        self.leName.setMaxLength(25)

        self.horizontalLayout.addWidget(self.leName)

        self.leConnetionStr = QLineEdit(Form)
        self.leConnetionStr.setObjectName(u"leConnetionStr")
        sizePolicy.setHeightForWidth(self.leConnetionStr.sizePolicy().hasHeightForWidth())
        self.leConnetionStr.setSizePolicy(sizePolicy)
        self.leConnetionStr.setFont(font)

        self.horizontalLayout.addWidget(self.leConnetionStr)

        self.tbRun = QToolButton(Form)
        self.tbRun.setObjectName(u"tbRun")
        self.tbRun.setMinimumSize(QSize(28, 28))
        self.tbRun.setMaximumSize(QSize(28, 28))
        font1 = QFont()
        font1.setFamilies([u"DejaVu Sans Mono"])
        font1.setPointSize(12)
        font1.setBold(True)
        font1.setItalic(False)
        self.tbRun.setFont(font1)
        self.tbRun.setIconSize(QSize(36, 36))
        self.tbRun.setCheckable(True)
        self.tbRun.setChecked(False)

        self.horizontalLayout.addWidget(self.tbRun)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        font2 = QFont()
        font2.setFamilies([u"DejaVu Sans Mono"])
        font2.setPointSize(10)
        font2.setBold(True)
        font2.setItalic(False)
        self.tabWidget.setFont(font2)
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.tabWidget.setElideMode(Qt.ElideMiddle)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setTabBarAutoHide(False)
        self.tabWidgetPage1 = QWidget()
        self.tabWidgetPage1.setObjectName(u"tabWidgetPage1")
        self.verticalLayout_3 = QVBoxLayout(self.tabWidgetPage1)
        self.verticalLayout_3.setSpacing(1)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label = QLabel(self.tabWidgetPage1)
        self.label.setObjectName(u"label")
        self.label.setFont(font2)
        self.label.setIndent(5)

        self.horizontalLayout_5.addWidget(self.label)

        self.spSize = QSpinBox(self.tabWidgetPage1)
        self.spSize.setObjectName(u"spSize")
        sizePolicy.setHeightForWidth(self.spSize.sizePolicy().hasHeightForWidth())
        self.spSize.setSizePolicy(sizePolicy)
        self.spSize.setMinimumSize(QSize(100, 0))
        self.spSize.setFont(font2)
        self.spSize.setWrapping(False)
        self.spSize.setAlignment(Qt.AlignCenter)
        self.spSize.setReadOnly(False)
        self.spSize.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spSize.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.spSize.setProperty("showGroupSeparator", True)
        self.spSize.setMinimum(1)
        self.spSize.setMaximum(9999)
        self.spSize.setValue(1)

        self.horizontalLayout_5.addWidget(self.spSize)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_4 = QLabel(self.tabWidgetPage1)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font2)
        self.label_4.setIndent(5)

        self.horizontalLayout_6.addWidget(self.label_4)

        self.spInterval = QSpinBox(self.tabWidgetPage1)
        self.spInterval.setObjectName(u"spInterval")
        sizePolicy.setHeightForWidth(self.spInterval.sizePolicy().hasHeightForWidth())
        self.spInterval.setSizePolicy(sizePolicy)
        self.spInterval.setMinimumSize(QSize(100, 0))
        self.spInterval.setFont(font2)
        self.spInterval.setWrapping(False)
        self.spInterval.setAlignment(Qt.AlignCenter)
        self.spInterval.setReadOnly(False)
        self.spInterval.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spInterval.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.spInterval.setProperty("showGroupSeparator", True)
        self.spInterval.setMinimum(10)
        self.spInterval.setMaximum(999999)
        self.spInterval.setValue(250)

        self.horizontalLayout_6.addWidget(self.spInterval)

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.btnSendError = QPushButton(self.tabWidgetPage1)
        self.btnSendError.setObjectName(u"btnSendError")

        self.verticalLayout_3.addWidget(self.btnSendError)

        self.tabWidget.addTab(self.tabWidgetPage1, "")
        self.tabWidgetPage2 = QWidget()
        self.tabWidgetPage2.setObjectName(u"tabWidgetPage2")
        self.verticalLayout_2 = QVBoxLayout(self.tabWidgetPage2)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frmNoRead = QFrame(self.tabWidgetPage2)
        self.frmNoRead.setObjectName(u"frmNoRead")
        self.frmNoRead.setFrameShape(QFrame.StyledPanel)
        self.frmNoRead.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_3 = QHBoxLayout(self.frmNoRead)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.cbxNoRead = QCheckBox(self.frmNoRead)
        self.cbxNoRead.setObjectName(u"cbxNoRead")
        self.cbxNoRead.setFont(font2)

        self.horizontalLayout_3.addWidget(self.cbxNoRead)

        self.spNoReadPercent = QSpinBox(self.frmNoRead)
        self.spNoReadPercent.setObjectName(u"spNoReadPercent")
        sizePolicy.setHeightForWidth(self.spNoReadPercent.sizePolicy().hasHeightForWidth())
        self.spNoReadPercent.setSizePolicy(sizePolicy)
        self.spNoReadPercent.setMinimumSize(QSize(100, 0))
        self.spNoReadPercent.setFont(font2)
        self.spNoReadPercent.setWrapping(False)
        self.spNoReadPercent.setAlignment(Qt.AlignCenter)
        self.spNoReadPercent.setReadOnly(False)
        self.spNoReadPercent.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spNoReadPercent.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.spNoReadPercent.setProperty("showGroupSeparator", True)
        self.spNoReadPercent.setMinimum(0)
        self.spNoReadPercent.setMaximum(100)
        self.spNoReadPercent.setValue(0)

        self.horizontalLayout_3.addWidget(self.spNoReadPercent)

        self.horizontalLayout_3.setStretch(0, 1)

        self.verticalLayout_2.addWidget(self.frmNoRead)

        self.drmDuplicates = QFrame(self.tabWidgetPage2)
        self.drmDuplicates.setObjectName(u"drmDuplicates")
        self.drmDuplicates.setFrameShape(QFrame.StyledPanel)
        self.drmDuplicates.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_4 = QHBoxLayout(self.drmDuplicates)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.cbxDups = QCheckBox(self.drmDuplicates)
        self.cbxDups.setObjectName(u"cbxDups")
        self.cbxDups.setFont(font2)

        self.horizontalLayout_4.addWidget(self.cbxDups)

        self.spDupsPercent = QSpinBox(self.drmDuplicates)
        self.spDupsPercent.setObjectName(u"spDupsPercent")
        sizePolicy.setHeightForWidth(self.spDupsPercent.sizePolicy().hasHeightForWidth())
        self.spDupsPercent.setSizePolicy(sizePolicy)
        self.spDupsPercent.setMinimumSize(QSize(100, 0))
        self.spDupsPercent.setFont(font2)
        self.spDupsPercent.setWrapping(False)
        self.spDupsPercent.setAlignment(Qt.AlignCenter)
        self.spDupsPercent.setReadOnly(False)
        self.spDupsPercent.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spDupsPercent.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.spDupsPercent.setProperty("showGroupSeparator", True)
        self.spDupsPercent.setMinimum(0)
        self.spDupsPercent.setMaximum(100)
        self.spDupsPercent.setValue(0)

        self.horizontalLayout_4.addWidget(self.spDupsPercent)

        self.horizontalLayout_4.setStretch(0, 1)

        self.verticalLayout_2.addWidget(self.drmDuplicates)

        self.frmGrade = QFrame(self.tabWidgetPage2)
        self.frmGrade.setObjectName(u"frmGrade")
        self.frmGrade.setFrameShape(QFrame.StyledPanel)
        self.frmGrade.setFrameShadow(QFrame.Plain)
        self.horizontalLayout_2 = QHBoxLayout(self.frmGrade)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.cbxGrade = QCheckBox(self.frmGrade)
        self.cbxGrade.setObjectName(u"cbxGrade")
        self.cbxGrade.setFont(font2)

        self.horizontalLayout_2.addWidget(self.cbxGrade)

        self.spGradeErrorPercent = QSpinBox(self.frmGrade)
        self.spGradeErrorPercent.setObjectName(u"spGradeErrorPercent")
        sizePolicy.setHeightForWidth(self.spGradeErrorPercent.sizePolicy().hasHeightForWidth())
        self.spGradeErrorPercent.setSizePolicy(sizePolicy)
        self.spGradeErrorPercent.setMinimumSize(QSize(100, 0))
        self.spGradeErrorPercent.setFont(font2)
        self.spGradeErrorPercent.setWrapping(False)
        self.spGradeErrorPercent.setAlignment(Qt.AlignCenter)
        self.spGradeErrorPercent.setReadOnly(False)
        self.spGradeErrorPercent.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spGradeErrorPercent.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.spGradeErrorPercent.setProperty("showGroupSeparator", True)
        self.spGradeErrorPercent.setMinimum(0)
        self.spGradeErrorPercent.setMaximum(100)
        self.spGradeErrorPercent.setValue(0)

        self.horizontalLayout_2.addWidget(self.spGradeErrorPercent)

        self.horizontalLayout_2.setStretch(0, 1)

        self.verticalLayout_2.addWidget(self.frmGrade)

        self.tabWidget.addTab(self.tabWidgetPage2, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.tabWidget_2 = QTabWidget(Form)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tabWidget_2.setTabPosition(QTabWidget.North)
        self.tabWidget_2.setTabShape(QTabWidget.Triangular)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_5 = QVBoxLayout(self.tab)
        self.verticalLayout_5.setSpacing(1)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(1, 1, 1, 1)
        self.lstData = QListView(self.tab)
        self.lstData.setObjectName(u"lstData")
        font3 = QFont()
        font3.setFamilies([u"DejaVu Sans Mono"])
        font3.setPointSize(8)
        font3.setBold(False)
        font3.setItalic(False)
        self.lstData.setFont(font3)
        self.lstData.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstData.setDragDropMode(QAbstractItemView.DropOnly)
        self.lstData.setDefaultDropAction(Qt.MoveAction)
        self.lstData.setAlternatingRowColors(True)
        self.lstData.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lstData.setSelectionRectVisible(True)

        self.verticalLayout_5.addWidget(self.lstData)

        self.tabWidget_2.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_4 = QVBoxLayout(self.tab_2)
        self.verticalLayout_4.setSpacing(1)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(1, 1, 1, 1)
        self.lstProcessed = QListView(self.tab_2)
        self.lstProcessed.setObjectName(u"lstProcessed")
        self.lstProcessed.setFont(font3)
        self.lstProcessed.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstProcessed.setDragDropMode(QAbstractItemView.DragOnly)
        self.lstProcessed.setDefaultDropAction(Qt.MoveAction)
        self.lstProcessed.setAlternatingRowColors(True)
        self.lstProcessed.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lstProcessed.setResizeMode(QListView.Adjust)
        self.lstProcessed.setSelectionRectVisible(True)

        self.verticalLayout_4.addWidget(self.lstProcessed)

        self.tabWidget_2.addTab(self.tab_2, "")

        self.verticalLayout.addWidget(self.tabWidget_2)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Camera", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.leConnetionStr.setPlaceholderText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442 \u043f\u0440\u043e\u0441\u043b\u0443\u0448\u0438\u0432\u0430\u043d\u0438\u044f (9100, \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440)", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u041e\u0422\u041f\u0420\u0410\u0412\u041b\u042f\u0422\u042c \u0417\u0410 \u0420\u0410\u0417:", None))
        self.spSize.setSuffix(QCoreApplication.translate("Form", u" \u043a\u043c", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"\u041f\u0415\u0420\u0415\u0414\u0410\u0412\u0410\u0422\u042c \u041a\u0410\u0416\u0414\u042b\u0415:", None))
        self.spInterval.setSuffix(QCoreApplication.translate("Form", u" \u043c\u0441", None))
        self.btnSendError.setText(QCoreApplication.translate("Form", u"\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c error", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage1), QCoreApplication.translate("Form", u"\u041e\u0431\u043c\u0435\u043d", None))
        self.cbxNoRead.setText(QCoreApplication.translate("Form", u"NO READ", None))
        self.spNoReadPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.cbxDups.setText(QCoreApplication.translate("Form", u"\u0414\u0423\u0411\u041b\u042c", None))
        self.spDupsPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.cbxGrade.setText(QCoreApplication.translate("Form", u"\u0413\u0420\u0415\u0419\u0414", None))
        self.spGradeErrorPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage2), QCoreApplication.translate("Form", u"\u041e\u0448\u0438\u0431\u043a\u0438", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab), QCoreApplication.translate("Form", u"IN", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), QCoreApplication.translate("Form", u"OUT", None))
    # retranslateUi

