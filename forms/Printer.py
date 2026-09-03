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

        self.lstData = QListView(Form)
        self.lstData.setObjectName(u"lstData")
        self.lstData.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lstData.setDragDropMode(QAbstractItemView.DragOnly)
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
        self.verticalLayoutAdvanced = QVBoxLayout(self.wAdvanced)
        self.verticalLayoutAdvanced.setSpacing(1)
        self.verticalLayoutAdvanced.setObjectName(u"verticalLayoutAdvanced")
        self.verticalLayoutAdvanced.setContentsMargins(0, 0, 0, 0)
        self.leConnetionStr = QLineEdit(self.wAdvanced)
        self.leConnetionStr.setObjectName(u"leConnetionStr")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.leConnetionStr.sizePolicy().hasHeightForWidth())
        self.leConnetionStr.setSizePolicy(sizePolicy2)

        self.verticalLayoutAdvanced.addWidget(self.leConnetionStr)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(self.wAdvanced)
        self.label.setObjectName(u"label")
        self.label.setIndent(5)

        self.horizontalLayout_2.addWidget(self.label)

        self.spAmount = QSpinBox(self.wAdvanced)
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

        self.verticalLayoutAdvanced.addLayout(self.horizontalLayout_2)


        self.verticalLayout.addWidget(self.wAdvanced)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Printer", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
#if QT_CONFIG(tooltip)
        self.tbDelete.setToolTip(QCoreApplication.translate("Form", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.tbDelete.setText(QCoreApplication.translate("Form", u"X", None))
        self.tbAdvanced.setText(QCoreApplication.translate("Form", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u043e", None))
        self.leConnetionStr.setPlaceholderText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442 \u043f\u0440\u043e\u0441\u043b\u0443\u0448\u0438\u0432\u0430\u043d\u0438\u044f (9100, \u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440)", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u0411\u0443\u0444\u0435\u0440:", None))
    # retranslateUi

