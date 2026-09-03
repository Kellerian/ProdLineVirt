# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Generator.ui'
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
    QLabel, QLineEdit, QSizePolicy, QSpinBox,
    QToolButton, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(280, 130)
        Form.setMinimumSize(QSize(200, 130))
        Form.setMaximumSize(QSize(280, 16777215))
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leName = QLineEdit(Form)
        self.leName.setObjectName(u"leName")
        self.leName.setMaxLength(25)

        self.horizontalLayout.addWidget(self.leName)

        self.tbRun = QToolButton(Form)
        self.tbRun.setObjectName(u"tbRun")
        self.tbRun.setMinimumSize(QSize(28, 28))
        self.tbRun.setMaximumSize(QSize(28, 28))
        self.tbRun.setCheckable(True)

        self.horizontalLayout.addWidget(self.tbRun)

        self.tbDelete = QToolButton(Form)
        self.tbDelete.setObjectName(u"tbDelete")
        self.tbDelete.setMinimumSize(QSize(28, 28))
        self.tbDelete.setMaximumSize(QSize(28, 28))

        self.horizontalLayout.addWidget(self.tbDelete)

        self.horizontalLayout.setStretch(0, 4)

        self.verticalLayout.addLayout(self.horizontalLayout)

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
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(1)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_4 = QLabel(self.wAdvanced)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_6.addWidget(self.label_4)

        self.spInterval = QSpinBox(self.wAdvanced)
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

        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 1)

        self.verticalLayoutAdvanced.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_type = QHBoxLayout()
        self.horizontalLayout_type.setSpacing(1)
        self.horizontalLayout_type.setObjectName(u"horizontalLayout_type")
        self.label_5 = QLabel(self.wAdvanced)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_type.addWidget(self.label_5)

        self.cbxCodeType = QComboBox(self.wAdvanced)
        self.cbxCodeType.setObjectName(u"cbxCodeType")
        self.cbxCodeType.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_type.addWidget(self.cbxCodeType)

        self.horizontalLayout_type.setStretch(1, 1)

        self.verticalLayoutAdvanced.addLayout(self.horizontalLayout_type)

        self.horizontalLayout_to = QHBoxLayout()
        self.horizontalLayout_to.setSpacing(1)
        self.horizontalLayout_to.setObjectName(u"horizontalLayout_to")
        self.label_6 = QLabel(self.wAdvanced)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_to.addWidget(self.label_6)

        self.cbxTo = QComboBox(self.wAdvanced)
        self.cbxTo.setObjectName(u"cbxTo")
        self.cbxTo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_to.addWidget(self.cbxTo)

        self.horizontalLayout_to.setStretch(1, 1)

        self.verticalLayoutAdvanced.addLayout(self.horizontalLayout_to)

        self.horizontalLayout_gtin = QHBoxLayout()
        self.horizontalLayout_gtin.setSpacing(1)
        self.horizontalLayout_gtin.setObjectName(u"horizontalLayout_gtin")
        self.horizontalLayout_gtin.setContentsMargins(-1, 0, 0, 0)
        self.label_7 = QLabel(self.wAdvanced)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_gtin.addWidget(self.label_7)

        self.leGtin = QLineEdit(self.wAdvanced)
        self.leGtin.setObjectName(u"leGtin")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leGtin.sizePolicy().hasHeightForWidth())
        self.leGtin.setSizePolicy(sizePolicy1)
        self.leGtin.setMinimumSize(QSize(249, 0))
        self.leGtin.setMaximumSize(QSize(249, 16777215))
        self.leGtin.setMaxLength(14)
        self.leGtin.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_gtin.addWidget(self.leGtin)

        self.horizontalLayout_gtin.setStretch(1, 1)

        self.verticalLayoutAdvanced.addLayout(self.horizontalLayout_gtin)


        self.verticalLayout.addWidget(self.wAdvanced)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
#if QT_CONFIG(tooltip)
        self.tbDelete.setToolTip(QCoreApplication.translate("Form", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.tbDelete.setText(QCoreApplication.translate("Form", u"X", None))
        self.tbAdvanced.setText(QCoreApplication.translate("Form", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u043e", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"\u041d\u041e\u0412\u042b\u0419 \u041a\u041e\u0414 \u041a\u0410\u0416\u0414\u042b\u0415:", None))
        self.spInterval.setSuffix(QCoreApplication.translate("Form", u" \u043c\u0441", None))
        self.label_5.setText(QCoreApplication.translate("Form", u" \u0424:", None))
        self.label_6.setText(QCoreApplication.translate("Form", u" \u0412:", None))
        self.label_7.setText(QCoreApplication.translate("Form", u" G:", None))
        self.leGtin.setInputMask(QCoreApplication.translate("Form", u"00000000000000", None))
        self.leGtin.setText("")
        self.leGtin.setPlaceholderText(QCoreApplication.translate("Form", u"GTIN \u043f\u0440\u043e\u0434\u0443\u043a\u0446\u0438\u0438", None))
    # retranslateUi

