# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Controller.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QComboBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(260, 280)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(260, 280))
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
"QPushButton {\n"
"	border: 1px solid #FF17365D;\n"
"    border-radius: 3px;\n"
"	background-color: #226091;\n"
"	padding: 3px;\n"
"	color: #FFFFFF;\n"
"	font: bold 10pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"	color: #f0b321;\n"
"}\n"
"\n"
"QPushButton:pressed,\n"
"QPushButton:checked {\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
"	border: 2px solid #f0b321;\n"
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
"QTableWidget {\n"
"	font: 8pt \"DejaVu Sans Mono\";\n"
"}\n"
"\n"
"QToolButton:pressed,\n"
"QToolButton:checke"
                        "d {\n"
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
"    padding-left:"
                        " 4px;\n"
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
"    left: 1px;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    selection-background-color: #f0b321;\n"
"	selection-color: #19466a;\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
"	border: 2px solid #f0b321;\n"
"}\n"
"\n"
"QComboBox::item {\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
"}\n"
"\n"
"QComboBox::item:hover {\n"
"	background-color: #226091;\n"
"}\n"
"\n"
"QComboBox::item:selected {\n"
"	background-color: #f0b321;\n"
"	color: #19466a;\n"
"}\n"
"\n"
"QComboBox QToolTip {\n"
"    font: bold 10pt \"DejaVu Sans Mono\";\n"
"	color: #f0b321;\n"
"	background-color: #19466a;\n"
""
                        "	border: 2px solid #f0b321;\n"
"    border-radius: 3px;\n"
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
"	width: 0px;\n"
"}\n"
"\n"
"QWidget#Form {\n"
"	border: 1px solid #17365D;\n"
"	border-radius: 3px;\n"
"}")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leName = QLineEdit(Form)
        self.leName.setObjectName(u"leName")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
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

        self.lePort = QLineEdit(Form)
        self.lePort.setObjectName(u"lePort")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lePort.sizePolicy().hasHeightForWidth())
        self.lePort.setSizePolicy(sizePolicy2)
        self.lePort.setFont(font)

        self.horizontalLayout.addWidget(self.lePort)

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

        self.tbDelete = QToolButton(Form)
        self.tbDelete.setObjectName(u"tbDelete")
        self.tbDelete.setMinimumSize(QSize(28, 28))
        self.tbDelete.setMaximumSize(QSize(28, 28))
        self.tbDelete.setFont(font1)
        self.tbDelete.setIconSize(QSize(16, 16))

        self.horizontalLayout.addWidget(self.tbDelete)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayoutQueue = QHBoxLayout()
        self.horizontalLayoutQueue.setSpacing(0)
        self.horizontalLayoutQueue.setObjectName(u"horizontalLayoutQueue")
        self.labelQueue = QLabel(Form)
        self.labelQueue.setObjectName(u"labelQueue")
        sizePolicy1.setHeightForWidth(self.labelQueue.sizePolicy().hasHeightForWidth())
        self.labelQueue.setSizePolicy(sizePolicy1)
        font2 = QFont()
        font2.setFamilies([u"DejaVu Sans Mono"])
        font2.setPointSize(10)
        font2.setBold(True)
        font2.setItalic(False)
        self.labelQueue.setFont(font2)
        self.labelQueue.setIndent(5)

        self.horizontalLayoutQueue.addWidget(self.labelQueue)

        self.spQueueSize = QSpinBox(Form)
        self.spQueueSize.setObjectName(u"spQueueSize")
        sizePolicy2.setHeightForWidth(self.spQueueSize.sizePolicy().hasHeightForWidth())
        self.spQueueSize.setSizePolicy(sizePolicy2)
        self.spQueueSize.setMinimumSize(QSize(80, 0))
        self.spQueueSize.setAlignment(Qt.AlignCenter)
        self.spQueueSize.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spQueueSize.setMinimum(1)
        self.spQueueSize.setMaximum(1000)
        self.spQueueSize.setValue(10)

        self.horizontalLayoutQueue.addWidget(self.spQueueSize)

        self.horizontalLayoutQueue.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayoutQueue)

        self.horizontalLayoutModeType = QHBoxLayout()
        self.horizontalLayoutModeType.setSpacing(2)
        self.horizontalLayoutModeType.setObjectName(u"horizontalLayoutModeType")
        self.labelMode = QLabel(Form)
        self.labelMode.setObjectName(u"labelMode")
        sizePolicy1.setHeightForWidth(self.labelMode.sizePolicy().hasHeightForWidth())
        self.labelMode.setSizePolicy(sizePolicy1)
        self.labelMode.setFont(font2)
        self.labelMode.setIndent(5)

        self.horizontalLayoutModeType.addWidget(self.labelMode)

        self.cbMode = QComboBox(Form)
        self.cbMode.addItem("")
        self.cbMode.addItem("")
        self.cbMode.setObjectName(u"cbMode")
        sizePolicy2.setHeightForWidth(self.cbMode.sizePolicy().hasHeightForWidth())
        self.cbMode.setSizePolicy(sizePolicy2)
        self.cbMode.setFont(font2)

        self.horizontalLayoutModeType.addWidget(self.cbMode)

        self.labelType = QLabel(Form)
        self.labelType.setObjectName(u"labelType")
        sizePolicy1.setHeightForWidth(self.labelType.sizePolicy().hasHeightForWidth())
        self.labelType.setSizePolicy(sizePolicy1)
        self.labelType.setFont(font2)

        self.horizontalLayoutModeType.addWidget(self.labelType)

        self.cbType = QComboBox(Form)
        self.cbType.addItem("")
        self.cbType.addItem("")
        self.cbType.setObjectName(u"cbType")
        sizePolicy2.setHeightForWidth(self.cbType.sizePolicy().hasHeightForWidth())
        self.cbType.setSizePolicy(sizePolicy2)
        self.cbType.setFont(font2)

        self.horizontalLayoutModeType.addWidget(self.cbType)

        self.horizontalLayoutModeType.setStretch(1, 1)
        self.horizontalLayoutModeType.setStretch(3, 1)

        self.verticalLayout.addLayout(self.horizontalLayoutModeType)

        self.btnAddRegister = QPushButton(Form)
        self.btnAddRegister.setObjectName(u"btnAddRegister")
        sizePolicy2.setHeightForWidth(self.btnAddRegister.sizePolicy().hasHeightForWidth())
        self.btnAddRegister.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.btnAddRegister)

        self.tblRegisters = QTableWidget(Form)
        if (self.tblRegisters.columnCount() < 2):
            self.tblRegisters.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.tblRegisters.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tblRegisters.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.tblRegisters.setObjectName(u"tblRegisters")
        self.tblRegisters.setMinimumSize(QSize(0, 120))
        self.tblRegisters.setAlternatingRowColors(True)
        self.tblRegisters.setShowGrid(True)
        self.tblRegisters.setWordWrap(False)
        self.tblRegisters.setColumnCount(2)
        self.tblRegisters.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tblRegisters.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tblRegisters.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.tblRegisters.horizontalHeader().setVisible(True)
        self.tblRegisters.horizontalHeader().setMinimumSectionSize(1)
        self.tblRegisters.horizontalHeader().setStretchLastSection(True)
        self.tblRegisters.verticalHeader().setVisible(True)

        self.verticalLayout.addWidget(self.tblRegisters)

        self.verticalLayout.setStretch(4, 1)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Controller", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.lePort.setPlaceholderText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442 \u043f\u0440\u043e\u0441\u043b\u0443\u0448\u0438\u0432\u0430\u043d\u0438\u044f (\u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440 502)", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
#if QT_CONFIG(tooltip)
        self.tbDelete.setToolTip(QCoreApplication.translate("Form", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.tbDelete.setText(QCoreApplication.translate("Form", u"X", None))
        self.labelQueue.setText(QCoreApplication.translate("Form", u"\u041e\u0447\u0435\u0440\u0435\u0434\u044c:", None))
        self.labelMode.setText(QCoreApplication.translate("Form", u"\u0420\u0435\u0436\u0438\u043c:", None))
        self.cbMode.setItemText(0, QCoreApplication.translate("Form", u"Simplex", None))
        self.cbMode.setItemText(1, QCoreApplication.translate("Form", u"Duplex", None))

#if QT_CONFIG(tooltip)
        self.cbMode.setToolTip(QCoreApplication.translate("Form", u"\u0420\u0435\u0436\u0438\u043c \u043b\u0438\u043d\u0438\u0438 Doypack", None))
#endif // QT_CONFIG(tooltip)
        self.labelType.setText(QCoreApplication.translate("Form", u"\u0422\u0438\u043f:", None))
        self.cbType.setItemText(0, QCoreApplication.translate("Form", u"Delta", None))
        self.cbType.setItemText(1, QCoreApplication.translate("Form", u"Xinje", None))

#if QT_CONFIG(tooltip)
        self.cbType.setToolTip(QCoreApplication.translate("Form", u"\u041a\u0430\u0440\u0442\u0430 \u0440\u0435\u0433\u0438\u0441\u0442\u0440\u043e\u0432 \u041f\u041b\u041a", None))
#endif // QT_CONFIG(tooltip)
        self.btnAddRegister.setText(QCoreApplication.translate("Form", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u0443\u044e", None))
        ___qtablewidgetitem = self.tblRegisters.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Form", u"\u041f\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u0430\u044f", None));
        ___qtablewidgetitem1 = self.tblRegisters.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Form", u"\u0417\u043d\u0430\u0447\u0435\u043d\u0438\u0435", None));
#if QT_CONFIG(tooltip)
        self.tblRegisters.setToolTip(QCoreApplication.translate("Form", u"\u0410\u0434\u0440\u0435\u0441\u0430 holding 0\u202610000. \u041e\u0447\u0435\u0440\u0435\u0434\u044c Delta: \u0441 4146, \u0448\u0430\u0433 2 \u043f\u0440\u0438 Duplex (1 \u043f\u0440\u0438 Simplex). Xinje: \u0441 20.", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

