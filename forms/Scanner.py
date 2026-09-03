# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Scanner.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QHBoxLayout,
    QLineEdit, QListView, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget)

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
        Form.setMinimumSize(QSize(200, 250))
        Form.setMaximumSize(QSize(260, 16777215))
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
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
        self.leName.setMaxLength(25)

        self.horizontalLayout.addWidget(self.leName)

        self.tbRun = QToolButton(Form)
        self.tbRun.setObjectName(u"tbRun")
        self.tbRun.setMinimumSize(QSize(28, 28))
        self.tbRun.setMaximumSize(QSize(28, 28))
        self.tbRun.setIconSize(QSize(36, 36))
        self.tbRun.setCheckable(True)
        self.tbRun.setChecked(False)

        self.horizontalLayout.addWidget(self.tbRun)

        self.tbDelete = QToolButton(Form)
        self.tbDelete.setObjectName(u"tbDelete")
        self.tbDelete.setMinimumSize(QSize(28, 28))
        self.tbDelete.setMaximumSize(QSize(28, 28))
        self.tbDelete.setIconSize(QSize(16, 16))

        self.horizontalLayout.addWidget(self.tbDelete)

        self.horizontalLayout.setStretch(0, 4)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.leManualInput = QLineEdit(Form)
        self.leManualInput.setObjectName(u"leManualInput")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.leManualInput.sizePolicy().hasHeightForWidth())
        self.leManualInput.setSizePolicy(sizePolicy2)
        self.leManualInput.setClearButtonEnabled(True)

        self.horizontalLayout_2.addWidget(self.leManualInput)

        self.btnSend = QToolButton(Form)
        self.btnSend.setObjectName(u"btnSend")
        self.btnSend.setMinimumSize(QSize(28, 28))
        self.btnSend.setMaximumSize(QSize(28, 28))
        self.btnSend.setIconSize(QSize(16, 16))

        self.horizontalLayout_2.addWidget(self.btnSend)

        self.horizontalLayout_2.setStretch(0, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.lstData = QListView(Form)
        self.lstData.setObjectName(u"lstData")
        self.lstData.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstData.setDragDropMode(QAbstractItemView.DropOnly)
        self.lstData.setDefaultDropAction(Qt.MoveAction)
        self.lstData.setAlternatingRowColors(True)
        self.lstData.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lstData.setSelectionRectVisible(True)

        self.verticalLayout.addWidget(self.lstData)

        self.tbAdvanced = QToolButton(Form)
        self.tbAdvanced.setObjectName(u"tbAdvanced")
        self.tbAdvanced.setCheckable(True)
        self.tbAdvanced.setChecked(False)

        self.verticalLayout.addWidget(self.tbAdvanced)

        self.wAdvanced = QWidget(Form)
        self.wAdvanced.setObjectName(u"wAdvanced")
        self.wAdvanced.setVisible(False)
        self.horizontalLayoutAdvanced = QHBoxLayout(self.wAdvanced)
        self.horizontalLayoutAdvanced.setSpacing(1)
        self.horizontalLayoutAdvanced.setObjectName(u"horizontalLayoutAdvanced")
        self.horizontalLayoutAdvanced.setContentsMargins(0, 0, 0, 0)
        self.cbxComPort = QComboBox(self.wAdvanced)
        self.cbxComPort.addItem("")
        self.cbxComPort.setObjectName(u"cbxComPort")
        sizePolicy2.setHeightForWidth(self.cbxComPort.sizePolicy().hasHeightForWidth())
        self.cbxComPort.setSizePolicy(sizePolicy2)

        self.horizontalLayoutAdvanced.addWidget(self.cbxComPort)

        self.tbRefreshPorts = QToolButton(self.wAdvanced)
        self.tbRefreshPorts.setObjectName(u"tbRefreshPorts")
        self.tbRefreshPorts.setMinimumSize(QSize(28, 28))
        self.tbRefreshPorts.setMaximumSize(QSize(28, 28))
        self.tbRefreshPorts.setIconSize(QSize(16, 16))

        self.horizontalLayoutAdvanced.addWidget(self.tbRefreshPorts)


        self.verticalLayout.addWidget(self.wAdvanced)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Scanner", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
#if QT_CONFIG(tooltip)
        self.tbDelete.setToolTip(QCoreApplication.translate("Form", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.tbDelete.setText(QCoreApplication.translate("Form", u"X", None))
        self.leManualInput.setPlaceholderText(QCoreApplication.translate("Form", u"\u0420\u0443\u0447\u043d\u043e\u0439 \u0432\u0432\u043e\u0434 \u0442\u0435\u043a\u0441\u0442\u0430", None))
        self.btnSend.setText(QCoreApplication.translate("Form", u"\u25b6", None))
#if QT_CONFIG(tooltip)
        self.btnSend.setToolTip(QCoreApplication.translate("Form", u"\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lstData.setToolTip(QCoreApplication.translate("Form", u"\u0421\u043f\u0438\u0441\u043e\u043a \u043e\u0447\u0435\u0440\u0435\u0434\u0438 (\u043f\u0435\u0440\u0435\u0442\u0430\u0449\u0438\u0442\u0435 \u043a\u043e\u0434\u044b \u0441\u044e\u0434\u0430)", None))
#endif // QT_CONFIG(tooltip)
        self.tbAdvanced.setText(QCoreApplication.translate("Form", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u043e", None))
        self.cbxComPort.setItemText(0, QCoreApplication.translate("Form", u"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u043e\u0440\u0442", None))

#if QT_CONFIG(tooltip)
        self.cbxComPort.setToolTip(QCoreApplication.translate("Form", u"COM-\u043f\u043e\u0440\u0442", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.tbRefreshPorts.setToolTip(QCoreApplication.translate("Form", u"\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u043f\u0438\u0441\u043e\u043a COM-\u043f\u043e\u0440\u0442\u043e\u0432", None))
#endif // QT_CONFIG(tooltip)
        self.tbRefreshPorts.setText(QCoreApplication.translate("Form", u"\u21bb", None))
    # retranslateUi

