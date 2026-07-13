from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QLabel, QListView, QMessageBox, QWidget
from core.scanning.camera_proxy import CameraProxy
from core.scanning.data import CameraConfig, CameraParams
from forms.Camera import Ui_Form
from libs.code_scheduler import CodeScheduler
from libs.datamatrix import get_gs1dm_pixmap
from libs.model_processing import (
    CustomItemModel,
    count_ready_prefix,
    create_code_item,
    stamp_item,
)


class CameraWidget(QWidget, Ui_Form):
    """Виджет эмулятора камеры на холсте Line Emulator."""

    delete_requested = Signal()

    def __init__(self, name: str, port: int):
        super().__init__()
        self.setupUi(self)
        self._setup_icon(self.tbRun.isChecked())
        self.name = name
        self.model_in = CustomItemModel()
        self.model_out = QStandardItemModel()

        self.lstData.setModel(self.model_in)
        self.lstData.setAcceptDrops(True)
        self.lstData.setDropIndicatorShown(True)

        self.lstProcessed.setModel(self.model_out)
        self.lstProcessed.setDragEnabled(True)
        self._camera = self._get_camera_proxy()
        self._scheduler = CodeScheduler()
        self.model_in.rowsInserted.connect(self._on_model_in_rows_inserted)
        self._connect_ui()
        self.leName.setText(name)
        self.leConnetionStr.setText(str(port))
        self._lbl: QLabel | None = None

    def send_data(self) -> None:
        """Send a batch when the leading FIFO prefix is ready for transfer."""
        batch_size = self.spSize.value()
        interval = self.spInterval.value()
        self.lstData.setToolTip(
            f"Данных на отправку {self.model_in.rowCount()}"
        )
        self.lstProcessed.setToolTip(
            f"Данных обработано {self.model_out.rowCount()}"
        )
        if self.model_in.rowCount() < batch_size:
            return

        ready_count = count_ready_prefix(self.model_in, interval)
        if ready_count < batch_size:
            return

        data_to_send: list[str] = []
        for _ in range(batch_size):
            row = self.model_in.takeRow(0)
            item = row[0]
            data_to_send.append(item.text())
        self._camera.send_data(data_to_send)

    def _on_model_in_rows_inserted(
        self, parent: QModelIndex, first: int, last: int
    ) -> None:
        """Re-stamp items moved into the input queue (e.g. drag from processed list)."""
        del parent
        for row in range(first, last + 1):
            item = self.model_in.item(row, 0)
            if item is not None:
                stamp_item(item)

    def _connect_ui(self):
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.tbDelete.clicked.connect(self._on_delete_clicked)

        self.cbxNoRead.toggled.connect(self.set_no_read_settings)
        self.spNoReadPercent.valueChanged.connect(self.set_no_read_settings)

        self.cbxDups.toggled.connect(self.set_dups_settings)
        self.spDupsPercent.valueChanged.connect(self.set_dups_settings)

        self.cbxGrade.toggled.connect(self.set_grade_settings)
        self.spGradeErrorPercent.valueChanged.connect(self.set_grade_settings)
        self.lstData.doubleClicked.connect(self.create_image)
        self.lstProcessed.doubleClicked.connect(self.create_image)

        self.btnSendError.clicked.connect(self._send_error)
        self.tbCoords.toggled.connect(self.set_coords_option)

    def _on_delete_clicked(self) -> None:
        """Запрашивает подтверждение удаления; эмитит сигнал, если виджет остановлен."""
        if self.tbRun.isChecked():
            QMessageBox.warning(
                self,
                "Удаление",
                "Остановите виджет перед удалением",
            )
            return
        name = self.leName.text().strip() or self.name
        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить виджет «{name}»?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit()

    def _send_error(self):
        self.model_in.appendRow(create_code_item('error'))

    def _get_camera_proxy(self) -> CameraProxy:
        cp = CameraProxy()
        cp.scanned.connect(self.populate_scanned_data)
        return cp

    def populate_scanned_data(self, data: list[str]):
        for row in data:
            self.model_out.appendRow(create_code_item(row))

    def set_no_read_settings(self):
        self._camera.set_noread(
            self.cbxNoRead.isChecked(), self.spNoReadPercent.value()
        )

    def set_grade_settings(self):
        self._camera.set_grade(
            self.cbxGrade.isChecked(), self.spGradeErrorPercent.value()
        )

    def set_dups_settings(self):
        self._camera.set_duplicates(
            self.cbxDups.isChecked(), self.spDupsPercent.value()
        )

    def set_coords_option(self):
        self._camera.set_coords_option(self.tbCoords.isChecked())

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def clear_data(self) -> None:
        """Clear input/output queues without stopping the emulator."""
        self.model_in.clear()
        self.model_out.clear()
        self._camera.clear_queues()

    def run(self, toggled: bool):
        if not self.leName.text() and not self.leConnetionStr.text():
            self.tbRun.setChecked(False)
            return
        self.leName.setDisabled(toggled)
        self.leConnetionStr.setDisabled(toggled)
        self.name = self.leName.text()
        if toggled:
            name = self.leName.text()
            try:
                port = int(self.leConnetionStr.text())
            except ValueError:
                return
            self._run_camera(name, port)
            self._scheduler.start(self.send_data)
        else:
            self._scheduler.stop()
            self._camera.stop()
            self.clear_data()

    def _run_camera(self, name: str, port: int):
        self._camera.start(name, port)
        self.set_no_read_settings()
        self.set_dups_settings()
        self.set_grade_settings()
        self.set_coords_option()

    def load_options(self, params: CameraParams):
        self.spSize.setValue(params.packet_size)
        self.spInterval.setValue(params.interval)
        self.cbxNoRead.setChecked(params.gen_no_read)
        self.spNoReadPercent.setValue(params.no_read_perc)
        self.cbxDups.setChecked(params.gen_duplicates)
        self.spDupsPercent.setValue(params.duplicates_perc)
        self.cbxGrade.setChecked(params.gen_grade)
        self.spDupsPercent.setValue(params.grade_perc)

    def options(self) -> CameraConfig:
        params = CameraParams(
            packet_size=self.spSize.value(),
            interval=self.spInterval.value(),
            gen_no_read=self.cbxNoRead.isChecked(),
            no_read_perc=self.spNoReadPercent.value(),
            gen_duplicates=self.cbxDups.isChecked(),
            duplicates_perc=self.spDupsPercent.value(),
            gen_grade=self.cbxGrade.isChecked(),
            grade_perc=self.spGradeErrorPercent.value()
        )
        return CameraConfig(
            name=self.name,
            port=int(self.leConnetionStr.text()),
            config=params
        )

    def create_image(self, idx: QModelIndex):
        sender: QListView = self.sender()
        model = sender.model()
        data = model.data(idx, Qt.ItemDataRole.DisplayRole)
        pix = get_gs1dm_pixmap(data)
        self._lbl = QLabel()
        self._lbl.setPixmap(pix)
        self._lbl.show()
