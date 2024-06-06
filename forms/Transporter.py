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
        Form.resize(218, 81)
        Form.setStyleSheet(u"QToolButton {\n"
"    qproperty-alignment: AlignCenter;\n"
"	border: 1px solid #FF17365D;\n"
"	background-color: #226091;\n"
"	padding: 3px;\n"
"	color: #FFFFFF;\n"
"	font: 10pt \"Arial Black\";\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"	color: #f0b321;\n"
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
"	font: 10pt \"Arial Black\";\n"
"}\n"
"\n"
"QSpinBox::up-button { subcontrol-origin: content;  subcontrol-position: right;  width:20px; height: 20px; }\n"
"QSpinBox::down-button {subcontrol-origin: content; subcontrol-position: left;  width:20px; height: 20px; }\n"
"")
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setFamilies([u"Arial Black"])
        font.setPointSize(10)
        font.setBold(True)
        self.label_3.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_3)

        self.cbxFrom = QComboBox(Form)
        self.cbxFrom.setObjectName(u"cbxFrom")
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.cbxFrom.setFont(font1)

        self.horizontalLayout_2.addWidget(self.cbxFrom)

        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        font2 = QFont()
        font2.setFamilies([u"Arial Black"])
        font2.setPointSize(10)
        self.label_2.setFont(font2)

        self.horizontalLayout.addWidget(self.label_2)

        self.cbxTo = QComboBox(Form)
        self.cbxTo.setObjectName(u"cbxTo")
        self.cbxTo.setFont(font1)

        self.horizontalLayout.addWidget(self.cbxTo)

        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)


        self.horizontalLayout_3.addLayout(self.verticalLayout)

        self.tbRun = QToolButton(Form)
        self.tbRun.setObjectName(u"tbRun")
        self.tbRun.setMinimumSize(QSize(28, 28))
        self.tbRun.setMaximumSize(QSize(28, 28))
        font3 = QFont()
        font3.setFamilies([u"Arial Black"])
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(False)
        self.tbRun.setFont(font3)
        self.tbRun.setIconSize(QSize(36, 36))
        self.tbRun.setCheckable(True)
        self.tbRun.setChecked(False)

        self.horizontalLayout_3.addWidget(self.tbRun)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font2)

        self.horizontalLayout_6.addWidget(self.label_4)

        self.spInterval = QSpinBox(Form)
        self.spInterval.setObjectName(u"spInterval")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spInterval.sizePolicy().hasHeightForWidth())
        self.spInterval.setSizePolicy(sizePolicy)
        self.spInterval.setMinimumSize(QSize(75, 0))
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

        self.verticalLayout_2.addLayout(self.horizontalLayout_6)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"\u0418\u0417:", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"\u0412:", None))
        self.tbRun.setText("")
        self.label_4.setText(QCoreApplication.translate("Form", u"\u0418\u041d\u0422\u0415\u0420\u0412\u0410\u041b:", None))
        self.spInterval.setSuffix(QCoreApplication.translate("Form", u" \u043c\u0441", None))
    # retranslateUi

