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
        Form.resize(200, 342)
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
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy)
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
        sizePolicy.setHeightForWidth(self.leConnetionStr.sizePolicy().hasHeightForWidth())
        self.leConnetionStr.setSizePolicy(sizePolicy)

        self.verticalLayoutAdvanced.addWidget(self.leConnetionStr)

        self.tabWidget = QTabWidget(self.wAdvanced)
        self.tabWidget.setObjectName(u"tabWidget")
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
        self.label.setIndent(5)

        self.horizontalLayout_5.addWidget(self.label)

        self.spSize = QSpinBox(self.tabWidgetPage1)
        self.spSize.setObjectName(u"spSize")
        sizePolicy.setHeightForWidth(self.spSize.sizePolicy().hasHeightForWidth())
        self.spSize.setSizePolicy(sizePolicy)
        self.spSize.setMinimumSize(QSize(100, 0))
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
        self.label_4.setIndent(5)

        self.horizontalLayout_6.addWidget(self.label_4)

        self.spInterval = QSpinBox(self.tabWidgetPage1)
        self.spInterval.setObjectName(u"spInterval")
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

        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setSpacing(1)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(-1, 0, -1, 0)
        self.btnSendError = QPushButton(self.tabWidgetPage1)
        self.btnSendError.setObjectName(u"btnSendError")

        self.horizontalLayout_7.addWidget(self.btnSendError)

        self.tbCoords = QToolButton(self.tabWidgetPage1)
        self.tbCoords.setObjectName(u"tbCoords")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tbCoords.sizePolicy().hasHeightForWidth())
        self.tbCoords.setSizePolicy(sizePolicy1)
        self.tbCoords.setMinimumSize(QSize(27, 27))
        self.tbCoords.setMaximumSize(QSize(58, 27))
        self.tbCoords.setCheckable(True)
        self.tbCoords.setChecked(False)
        self.tbCoords.setAutoExclusive(False)

        self.horizontalLayout_7.addWidget(self.tbCoords)

        self.horizontalLayout_7.setStretch(0, 1)

        self.verticalLayout_3.addLayout(self.horizontalLayout_7)

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

        self.verticalLayoutAdvanced.addWidget(self.tabWidget)


        self.verticalLayout.addWidget(self.wAdvanced)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Form)

        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Camera", None))
        self.leName.setPlaceholderText(QCoreApplication.translate("Form", u"\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", None))
        self.tbRun.setText(QCoreApplication.translate("Form", u"R", None))
#if QT_CONFIG(tooltip)
        self.tbDelete.setToolTip(QCoreApplication.translate("Form", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c", None))
#endif // QT_CONFIG(tooltip)
        self.tbDelete.setText(QCoreApplication.translate("Form", u"X", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab), QCoreApplication.translate("Form", u"IN", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), QCoreApplication.translate("Form", u"OUT", None))
        self.tbAdvanced.setText(QCoreApplication.translate("Form", u"\u0414\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u043e", None))
        self.leConnetionStr.setPlaceholderText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u041f\u0410\u041a\u0415\u0422", None))
        self.spSize.setSuffix(QCoreApplication.translate("Form", u" \u043a\u043c", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"\u0418\u041d\u0422\u0415\u0420\u0412\u0410\u041b", None))
        self.spInterval.setSuffix(QCoreApplication.translate("Form", u" \u043c\u0441", None))
        self.btnSendError.setText(QCoreApplication.translate("Form", u"error", None))
        self.tbCoords.setText(QCoreApplication.translate("Form", u"(x,y)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage1), QCoreApplication.translate("Form", u"\u041e\u0431\u043c\u0435\u043d", None))
        self.cbxNoRead.setText(QCoreApplication.translate("Form", u"NO READ", None))
        self.spNoReadPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.cbxDups.setText(QCoreApplication.translate("Form", u"\u0414\u0423\u0411\u041b\u042c", None))
        self.spDupsPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.cbxGrade.setText(QCoreApplication.translate("Form", u"\u0413\u0420\u0415\u0419\u0414", None))
        self.spGradeErrorPercent.setSuffix(QCoreApplication.translate("Form", u" %", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage2), QCoreApplication.translate("Form", u"\u041e\u0448\u0438\u0431\u043a\u0438", None))
    # retranslateUi

