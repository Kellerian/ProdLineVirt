from logging import getLogger
from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QComboBox, QWidget
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.transporting.data import TransporterConfig
from forms.Transporter import Ui_Form
from libs.loggers import UI_LOGGER
from libs.code_cleanup import get_clean_code


class TransporterWidget(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._log = getLogger(UI_LOGGER)
        self.name = f"TRW_{id(self)}"
        self._setup_icon(self.tbRun.isChecked())
        self._timer_sender = QTimer()
        self._connect_ui()
        self._device_data: dict[int, CameraWidget | PrinterWidget] = {}
        self.model_in: QStandardItemModel | None = None
        self.model_out: QStandardItemModel | None = None

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def _connect_ui(self):
        self.tbRun.toggled.connect(self.start)
        self.spInterval.valueChanged.connect(self.set_interval_settings)
        self._timer_sender.timeout.connect(self.send_data)
        self.cbxTo.currentIndexChanged.connect(self.set_to_model)
        self.cbxFrom.currentIndexChanged.connect(self.set_from_model)

    def _get_model_current_widget(
        self, cbx: QComboBox, idx: int
    ) -> CameraWidget | PrinterWidget | None:
        model = cbx.model()
        index = model.index(idx, 1)
        data = model.data(index, Qt.ItemDataRole.DisplayRole)
        if data is None:
            return None
        widget_id = int(data)
        widget = self._device_data.get(widget_id)
        return widget

    def set_from_model(self, idx: int | None = None):
        if idx is None:
            idx = self.cbxFrom.currentIndex()
        widget = self._get_model_current_widget(self.cbxFrom, idx)
        self.model_in = widget.model_out
        self._log.info(f"БЕРЁМ ИЗ {widget.name}")

    def set_to_model(self, idx: int | None = None):
        if idx is None:
            idx = self.cbxTo.currentIndex()
        widget = self._get_model_current_widget(self.cbxTo, idx)
        self.model_out = widget.model_in
        self._log.info(f"ПЕРЕДАЁМ В {widget.name}")

    @staticmethod
    def set_cbx_current_value(cbx: QComboBox, value: str):
        model = cbx.model()
        for row in range(model.rowCount()):
            index = model.index(row, 1)
            data = model.data(index, Qt.ItemDataRole.DisplayRole)
            if data == value:
                cbx.setCurrentIndex(row)
                return
        cbx.setCurrentIndex(0)

    def get_data_models(self) -> tuple[QStandardItemModel, QStandardItemModel]:
        from_model = QStandardItemModel()
        to_model = QStandardItemModel()
        for device in self._device_data.values():
            dev_name = device.name
            dev_id = id(device)
            from_model.appendRow(
                [QStandardItem(dev_name), QStandardItem(str(dev_id))]
            )
            if isinstance(device, CameraWidget):
                to_model.appendRow(
                    [QStandardItem(dev_name), QStandardItem(str(dev_id))]
                )
        return from_model, to_model

    def _set_cbx_model(self, cbx: QComboBox, model: QStandardItemModel):
        cbx.blockSignals(True)
        cur_wd = self._get_model_current_widget(cbx, cbx.currentIndex())
        cbx.setModel(model)
        cbx.setModelColumn(0)
        self.set_cbx_current_value(cbx, str(id(cur_wd)))
        cbx.blockSignals(False)

    def setup_models(
        self, device_widgets: dict[int, CameraWidget | PrinterWidget]
    ):
        if self.tbRun.isChecked():
            return
        self._device_data.update(device_widgets)
        from_model, to_model = self.get_data_models()
        self._set_cbx_model(self.cbxFrom, from_model)
        self._set_cbx_model(self.cbxTo, to_model)

    def set_source_ids(self, take_from_id: int, give_to: int):
        self.set_cbx_current_value(self.cbxFrom, str(take_from_id))
        self.set_cbx_current_value(self.cbxTo, str(give_to))

    def set_interval(self, value: int):
        self.spInterval.setValue(value)

    def start(self, toggled: bool):
        self._timer_sender.setInterval(self.spInterval.value())
        self._setup_icon(toggled)
        self.run(toggled)

    def set_interval_settings(self, value: int):
        self._timer_sender.setInterval(value)

    def send_data(self):
        if self.model_in is None or self.model_out is None:
            self._log.warning(
                f"Не заданы источники: IN:{self.model_in} OUT:{self.model_out}"
            )
            return
        if not self.model_in.rowCount():
            return
        row = self.model_in.takeRow(0)
        for i, _r in enumerate(row.copy()):
            row[i] = QStandardItem(get_clean_code(_r.text()))
        self.model_out.appendRow(row)

    def run(self, toggled: bool):
        if toggled:
            self._log.info(f"ТРАНСПОРТ СТАРТ")
            self.set_from_model()
            self.set_to_model()
            self._timer_sender.start()
        else:
            self._log.info(f"ТРАНСПОРТ ОСТАНОВКА")
            self._timer_sender.stop()
        self.cbxTo.setDisabled(toggled)
        self.cbxFrom.setDisabled(toggled)

    def options(self) -> TransporterConfig:
        from_wd = self._get_model_current_widget(
            self.cbxFrom, self.cbxFrom.currentIndex()
        )
        to_wd = self._get_model_current_widget(
            self.cbxTo, self.cbxTo.currentIndex()
        )
        return TransporterConfig(
            take_from=from_wd.name,
            give_to=to_wd.name,
            interval=self.spInterval.value()
        )
