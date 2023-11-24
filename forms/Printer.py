# Form implementation generated from reading ui file 'Printer.ui'
#
# Created by: PyQt6 UI code generator 6.6.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(270, 400)
        Form.setStyleSheet("QToolButton {\n"
"    qproperty-alignment: AlignCenter;\n"
"    border: 1px solid #FF17365D;\n"
"    background-color: #226091;\n"
"    padding: 3px;\n"
"    color: #FFFFFF;\n"
"    font: 10pt \"Arial Black\";\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"    color: #f0b321;\n"
"}\n"
"\n"
"QToolButton:pressed,\n"
"QToolButtont:checked {\n"
"    color: #f0b321;\n"
"    background-color: #19466a;\n"
"    border: 2px solid #f0b321;\n"
"}\n"
"\n"
"QSpinBox {\n"
"    qproperty-alignment: AlignCenter;\n"
"    border: 1px solid #FF17365D;\n"
"    color: #f0b321;\n"
"    background-color: #226091;\n"
"    border-radius: 3px;\n"
"    selection-background-color:#19466a;\n"
"    selection-color: #f0b321;\n"
"    font: 10pt \"Arial Black\";\n"
"}\n"
"\n"
"QSpinBox::up-button { subcontrol-origin: content;  subcontrol-position: right;  width:20px; height: 20px; }\n"
"QSpinBox::down-button {subcontrol-origin: content; subcontrol-position: left;  width:20px; height: 20px; }\n"
"")
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leConnetionStr = QtWidgets.QLineEdit(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leConnetionStr.sizePolicy().hasHeightForWidth())
        self.leConnetionStr.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.leConnetionStr.setFont(font)
        self.leConnetionStr.setObjectName("leConnetionStr")
        self.horizontalLayout.addWidget(self.leConnetionStr)
        self.tbRun = QtWidgets.QToolButton(parent=Form)
        self.tbRun.setMinimumSize(QtCore.QSize(28, 28))
        self.tbRun.setMaximumSize(QtCore.QSize(28, 28))
        font = QtGui.QFont()
        font.setFamily("Arial Black")
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.tbRun.setFont(font)
        self.tbRun.setText("")
        self.tbRun.setIconSize(QtCore.QSize(36, 36))
        self.tbRun.setCheckable(True)
        self.tbRun.setChecked(False)
        self.tbRun.setObjectName("tbRun")
        self.horizontalLayout.addWidget(self.tbRun)
        self.horizontalLayout.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.leName = QtWidgets.QLineEdit(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.leName.setFont(font)
        self.leName.setMaxLength(25)
        self.leName.setObjectName("leName")
        self.horizontalLayout_2.addWidget(self.leName)
        self.spAmount = QtWidgets.QSpinBox(parent=Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spAmount.sizePolicy().hasHeightForWidth())
        self.spAmount.setSizePolicy(sizePolicy)
        self.spAmount.setMinimumSize(QtCore.QSize(75, 0))
        self.spAmount.setWrapping(False)
        self.spAmount.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.spAmount.setReadOnly(False)
        self.spAmount.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spAmount.setCorrectionMode(QtWidgets.QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.spAmount.setProperty("showGroupSeparator", True)
        self.spAmount.setMinimum(1)
        self.spAmount.setMaximum(100)
        self.spAmount.setProperty("value", 1)
        self.spAmount.setObjectName("spAmount")
        self.horizontalLayout_2.addWidget(self.spAmount)
        self.horizontalLayout_2.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.lstData = QtWidgets.QListView(parent=Form)
        font = QtGui.QFont()
        font.setFamily("Arial Narrow")
        font.setPointSize(10)
        self.lstData.setFont(font)
        self.lstData.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lstData.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.lstData.setAlternatingRowColors(True)
        self.lstData.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.lstData.setSelectionRectVisible(True)
        self.lstData.setObjectName("lstData")
        self.verticalLayout.addWidget(self.lstData)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Printer"))
        self.leConnetionStr.setPlaceholderText(_translate("Form", "Порт прослушивания (9100, например)"))
        self.leName.setPlaceholderText(_translate("Form", "Название устройства"))
