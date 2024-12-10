# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Transporter.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QComboBox, QHBoxLayout,
    QLabel, QSizePolicy, QSpinBox, QToolButton,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(280, 100)
        Form.setMinimumSize(QSize(280, 100))
        Form.setMaximumSize(QSize(280, 100))
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
"QToolButton:checked {\n"
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
"QSpinBox::up-"
                        "button { subcontrol-origin: content;  subcontrol-position: right;  width:20px; height: 20px; }\n"
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
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(1)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")
        font = QFont()
        font.setFamilies([u"DejaVu Sans Mono"])
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        self.label_4.setFont(font)

        self.horizontalLayout_6.addWidget(self.label_4)

        self.spInterval = QSpinBox(Form)
        self.spInterval.setObjectName(u"spInterval")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spInterval.sizePolicy().hasHeightForWidth())
        self.spInterval.setSizePolicy(sizePolicy)
        self.spInterval.setMinimumSize(QSize(100, 0))
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

        self.horizontalLayout_6.addWidget(self.tbRun)

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_5 = QLabel(Form)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)

        self.horizontalLayout.addWidget(self.label_5)

        self.cbxFrom = QComboBox(Form)
        self.cbxFrom.setObjectName(u"cbxFrom")
        self.cbxFrom.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout.addWidget(self.cbxFrom)

        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_6 = QLabel(Form)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_6)

        self.cbxTo = QComboBox(Form)
        self.cbxTo.setObjectName(u"cbxTo")
        self.cbxTo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_2.addWidget(self.cbxTo)

        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"\u041f\u0415\u0420\u0415\u0414\u0410\u0412\u0410\u0422\u042c \u041a\u0410\u0416\u0414\u042b\u0415:", None))
        self.spInterval.setSuffix(QCoreApplication.translate("Form", u" \u043c\u0441", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"\u0418\u0417:", None))
        self.label_6.setText(QCoreApplication.translate("Form", u" \u0412:", None))
    # retranslateUi

