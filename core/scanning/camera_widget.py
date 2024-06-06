from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QWidget
from core.scanning.camera_proxy import CameraProxy
from forms.Camera import Ui_Form
from libs.model_processing import CustomItemModel


class CameraWidget(QWidget, Ui_Form):
    def __init__(self, name: str, port: int):
        super().__init__()
        self.setupUi(self)
        self._setup_icon(self.tbRun.isChecked())

        self.model_in = CustomItemModel()
        self.model_out = QStandardItemModel()

        self.lstData.setModel(self.model_in)
        self.lstData.setAcceptDrops(True)
        self.lstData.setDropIndicatorShown(True)

        self.lstProcessed.setModel(self.model_out)
        self.lstProcessed.setDragEnabled(True)
        self._camera = self._get_camera_proxy()
        self._timer_sender = QTimer()
        self._timer_sender.setInterval(self.spInterval.value())
        self._connect_ui()
        self.leName.setText(name)
        self.leConnetionStr.setText(str(port))

    def send_data(self):
        batch_size = self.spSize.value()
        if self.model_in.rowCount() < batch_size:
            return

        data_to_send: list[str] = []
        for _ in range(batch_size):
            row = self.model_in.takeRow(0)
            item = row[0]
            data_to_send.append(item.text())
        self._camera.send_data(data_to_send)

    def _connect_ui(self):
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)

        self.cbxNoRead.toggled.connect(self.set_no_read_settings)
        self.spNoReadPercent.valueChanged.connect(self.set_no_read_settings)

        self.cbxDups.toggled.connect(self.set_dups_settings)
        self.spDupsPercent.valueChanged.connect(self.set_dups_settings)

        self.cbxGrade.toggled.connect(self.set_grade_settings)
        self.spGradeErrorPercent.valueChanged.connect(self.set_grade_settings)
        self.spInterval.valueChanged.connect(self.set_interval_settings)
        # noinspection PyUnresolvedReferences
        self._timer_sender.timeout.connect(self.send_data)

    def _get_camera_proxy(self) -> CameraProxy:
        cp = CameraProxy()
        cp.scanned.connect(self.populate_scanned_data)
        return cp

    def populate_scanned_data(self, data: list[str]):
        for row in data:
            self.model_out.appendRow(QStandardItem(row))

    def set_no_read_settings(self):
        self._camera.set_noread(
            self.cbxNoRead.isChecked(), self.spNoReadPercent.value()
        )

    def set_grade_settings(self):
        self._camera.set_grade(
            self.cbxGrade.isChecked(), self.spGradeErrorPercent.value()
        )

    def set_interval_settings(self, value: int):
        self._timer_sender.setInterval(value)

    def set_dups_settings(self):
        self._camera.set_duplicates(
            self.cbxDups.isChecked(), self.spDupsPercent.value()
        )

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def _clear_data(self):
        self.model_in.clear()
        self.model_out.clear()

    def run(self, toggled: bool):
        if not self.leName.text() and not self.leConnetionStr.text():
            self.tbRun.setChecked(False)
            return
        self.leName.setDisabled(toggled)
        self.leConnetionStr.setDisabled(toggled)
        if toggled:
            name = self.leName.text()
            try:
                port = int(self.leConnetionStr.text())
            except ValueError:
                return
            self._run_camera(name, port)
            self._timer_sender.start()
        else:
            self._timer_sender.stop()
            self._camera.stop()
            self._clear_data()

    def _run_camera(self, name: str, port: int):
        self._camera.start(name, port)
        self.set_no_read_settings()
        self.set_dups_settings()
        self.set_grade_settings()
