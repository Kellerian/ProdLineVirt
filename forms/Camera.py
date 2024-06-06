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
    QListView, QSizePolicy, QSpinBox, QTabWidget,
    QToolButton, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(232, 253)
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
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        font = QFont()
        font.setFamilies([u"Arial Black"])
        font.setPointSize(8)
        font.setItalic(False)
        self.tabWidget.setFont(font)
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.tabWidget.setElideMode(Qt.ElideLeft)
        self.tabWidget.setDocumentMode(True)
        self.tabWidgetPage1 = QWidget()
        self.tabWidgetPage1.setObjectName(u"tabWidgetPage1")
        self.verticalLayout_3 = QVBoxLayout(self.tabWidgetPage1)
        self.verticalLayout_3.setSpacing(1)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leName = QLineEdit(self.tabWidgetPage1)
        self.leName.setObjectName(u"leName")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(12)
        self.leName.setFont(font1)
        self.leName.setMaxLength(25)

        self.horizontalLayout.addWidget(self.leName)

        self.leConnetionStr = QLineEdit(self.tabWidgetPage1)
        self.leConnetionStr.setObjectName(u"leConnetionStr")
        sizePolicy.setHeightForWidth(self.leConnetionStr.sizePolicy().hasHeightForWidth())
        self.leConnetionStr.setSizePolicy(sizePolicy)
        self.leConnetionStr.setFont(font1)

        self.horizontalLayout.addWidget(self.leConnetionStr)

        self.tbRun = QToolButton(self.tabWidgetPage1)
        self.tbRun.setObjectName(u"tbRun")
        self.tbRun.setMinimumSize(QSize(28, 28))
        self.tbRun.setMaximumSize(QSize(28, 28))
        font2 = QFont()
        font2.setFamilies([u"Arial Black"])
        font2.setPointSize(10)
        font2.setBold(False)
        font2.setItalic(False)
        self.tbRun.setFont(font2)
        self.tbRun.setIconSize(QSize(36, 36))
        self.tbRun.setCheckable(True)
        self.tbRun.setChecked(False)

        self.horizontalLayout.addWidget(self.tbRun)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label = QLabel(self.tabWidgetPage1)
        self.label.setObjectName(u"label")
        font3 = QFont()
        font3.setFamilies([u"Arial Black"])
        font3.setPointSize(10)
        self.label.setFont(font3)

        self.horizontalLayout_5.addWidget(self.label)

        self.spSize = QSpinBox(self.tabWidgetPage1)
        self.spSize.setObjectName(u"spSize")
        sizePolicy.setHeightForWidth(self.spSize.sizePolicy().hasHeightForWidth())
        self.spSize.setSizePolicy(sizePolicy)
        self.spSize.setMinimumSize(QSize(75, 0))
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
        self.label_4.setFont(font3)

        self.horizontalLayout_6.addWidget(self.label_4)

        self.spInterval = QSpinBox(self.tabWidgetPage1)
        self.spInterval.setObjectName(u"spInterval")
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

        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

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
        self.cbxNoRead.setFont(font3)

        self.horizontalLayout_3.addWidget(self.cbxNoRead)

        self.spNoReadPercent = QSpinBox(self.frmNoRead)
        self.spNoReadPercent.setObjectName(u"spNoReadPercent")
        sizePolicy.setHeightForWidth(self.spNoReadPercent.sizePolicy().hasHeightForWidth())
        self.spNoReadPercent.setSizePolicy(sizePolicy)
        self.spNoReadPercent.setMinimumSize(QSize(100, 0))
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
        self.cbxDups.setFont(font3)

        self.horizontalLayout_4.addWidget(self.cbxDups)

        self.spDupsPercent = QSpinBox(self.drmDuplicates)
        self.spDupsPercent.setObjectName(u"spDupsPercent")
        sizePolicy.setHeightForWidth(self.spDupsPercent.sizePolicy().hasHeightForWidth())
        self.spDupsPercent.setSizePolicy(sizePolicy)
        self.spDupsPercent.setMinimumSize(QSize(100, 0))
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
        self.cbxGrade.setFont(font3)

        self.horizontalLayout_2.addWidget(self.cbxGrade)

        self.spGradeErrorPercent = QSpinBox(self.frmGrade)
        self.spGradeErrorPercent.setObjectName(u"spGradeErrorPercent")
        sizePolicy.setHeightForWidth(self.spGradeErrorPercent.sizePolicy().hasHeightForWidth())
        self.spGradeErrorPercent.setSizePolicy(sizePolicy)
        self.spGradeErrorPercent.setMinimumSize(QSize(100, 0))
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

        self.lstData = QListView(Form)
        self.lstData.setObjectName(u"lstData")
        font4 = QFont()
        font4.setFamilies([u"Arial Narrow"])
        font4.setPointSize(10)
        self.lstData.setFont(font4)
        self.lstData.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstData.setDragDropMode(QAbstractItemView.DropOnly)
        self.lstData.setDefaultDropAction(Qt.MoveAction)
        self.lstData.setAlternatingRowColors(True)
        self.lstData.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lstData.setSelectionRectVisible(True)

        self.verticalLayout.addWidget(self.lstData)

        self.lstProcessed = QListView(Form)
        self.lstProcessed.setObjectName(u"lstProcessed")
        self.lstProcessed.setFont(font4)
        self.lstProcessed.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstProcessed.setDragDropMode(QAbstractItemView.DragOnly)
        self.lstProcessed.setDefaultDropAction(Qt.MoveAction)
        self.lstProcessed.setAlternatingRowColors(True)
        self.lstProcessed.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lstProcessed.setSelectionRectVisible(True)

        self.verticalLayout.addWidget(self.lstProcessed)

        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Camera", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.leConnetionStr.setPlaceholderText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442 \u043f\u0440\u043e\u0441\u043b\u0443\u0448\u0438\u0432\u0430\u043d\u0438\u044f (9100, \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440)", None))
        self.tbRun.setText("")
        self.label.setText(QCoreApplication.translate("Form", u"\u041f\u0410\u041a\u0415\u0422:", None))
        self.spSize.setSuffix(QCoreApplication.translate("Form", u" \u043a\u043c", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"\u0418\u041d\u0422\u0415\u0420\u0412\u0410\u041b:", None))
        self.spInterval.setSuffix(QCoreApplication.translate("Form", u" \u043c\u0441", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage1), QCoreApplication.translate("Form", u"\u041e\u0431\u043c\u0435\u043d", None))
        self.cbxNoRead.setText(QCoreApplication.translate("Form", u"NO READ", None))
        self.spNoReadPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.cbxDups.setText(QCoreApplication.translate("Form", u"\u0414\u0423\u0411\u041b\u042c", None))
        self.spDupsPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.cbxGrade.setText(QCoreApplication.translate("Form", u"\u0413\u0420\u0415\u0419\u0414", None))
        self.spGradeErrorPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage2), QCoreApplication.translate("Form", u"\u041e\u0448\u0438\u0431\u043a\u0438", None))
    # retranslateUi

