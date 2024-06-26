# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Printer.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QHBoxLayout,
    QLabel, QLineEdit, QListView, QSizePolicy,
    QSpinBox, QToolButton, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(260, 250)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(260, 250))
        Form.setMaximumSize(QSize(260, 16777215))
        Form.setStyleSheet(u"QToolButton {\n"
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
"QToolButton:hover {\n"
"	color: #f0b321;\n"
"}\n"
"\n"
"QListView {\n"
"	font: 8pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
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
"	selection-color: #f0b321;\n"
"	font: bold 10pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QSpinBox::up"
                        "-button { subcontrol-origin: content;  subcontrol-position: right;  width:20px; height: 20px; }\n"
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
"    border-bottom-right-radius: 5px;\n"
"}\n"
"\n"
"QComboBox::down-arrow:on {\n"
"    top: 1px;\n"
""
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
"QScrollBar:add-line {\n"
"	background:  none;\n"
"	border: none;\n"
"	height: 0px;	\n"
"	padding: 0;\n"
"	w"
                        "idth: 0px;\n"
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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy1)
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
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.leConnetionStr.sizePolicy().hasHeightForWidth())
        self.leConnetionStr.setSizePolicy(sizePolicy2)
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

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        font2 = QFont()
        font2.setFamilies([u"DejaVu Sans Mono"])
        font2.setPointSize(10)
        font2.setBold(True)
        font2.setItalic(False)
        self.label.setFont(font2)
        self.label.setIndent(5)

        self.horizontalLayout_2.addWidget(self.label)

        self.spAmount = QSpinBox(Form)
        self.spAmount.setObjectName(u"spAmount")
        sizePolicy2.setHeightForWidth(self.spAmount.sizePolicy().hasHeightForWidth())
        self.spAmount.setSizePolicy(sizePolicy2)
        self.spAmount.setMinimumSize(QSize(100, 0))
        self.spAmount.setWrapping(False)
        self.spAmount.setAlignment(Qt.AlignCenter)
        self.spAmount.setReadOnly(False)
        self.spAmount.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spAmount.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.spAmount.setProperty("showGroupSeparator", True)
        self.spAmount.setMinimum(1)
        self.spAmount.setMaximum(100)
        self.spAmount.setValue(1)

        self.horizontalLayout_2.addWidget(self.spAmount)

        self.horizontalLayout_2.setStretch(0, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.lstData = QListView(Form)
        self.lstData.setObjectName(u"lstData")
        font3 = QFont()
        font3.setFamilies([u"DejaVu Sans Mono"])
        font3.setPointSize(8)
        font3.setBold(False)
        font3.setItalic(False)
        self.lstData.setFont(font3)
        self.lstData.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstData.setDragDropMode(QAbstractItemView.DragOnly)
        self.lstData.setDefaultDropAction(Qt.MoveAction)
        self.lstData.setAlternatingRowColors(True)
        self.lstData.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lstData.setSelectionRectVisible(True)

        self.verticalLayout.addWidget(self.lstData)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Printer", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.leConnetionStr.setPlaceholderText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442 \u043f\u0440\u043e\u0441\u043b\u0443\u0448\u0438\u0432\u0430\u043d\u0438\u044f (9100, \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440)", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u0411\u0443\u0444\u0435\u0440:", None))
    # retranslateUi

