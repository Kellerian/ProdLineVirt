import time
from logging import getLogger

from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QComboBox, QWidget

from core.barcode_scanner.scanner_widget import ScannerWidget
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.transporting.data import TransporterConfig
from forms.Transporter import Ui_Form
from libs.code_cleanup import get_clean_code
from libs.code_scheduler import CodeScheduler
from libs.loggers import UI_LOGGER
from libs.model_processing import create_code_item, is_item_ready


class TransporterWidget(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._log = getLogger(UI_LOGGER)
        self.name = f"TRW_{id(self)}"
        self._setup_icon(self.tbRun.isChecked())
        self._code_scheduler = CodeScheduler()
        self._last_transferred_at: float | None = None
        self._connect_ui()
        self._device_data: dict[int, CameraWidget | PrinterWidget | ScannerWidget] = {}
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
        self.cbxTo.currentIndexChanged.connect(self.set_to_model)
        self.cbxFrom.currentIndexChanged.connect(self.set_from_model)

    def _get_model_current_widget(
        self, cbx: QComboBox, idx: int
    ) -> CameraWidget | PrinterWidget | ScannerWidget | None:
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
        if widget is None:
            self._log.warning(f"Не выбран источник: idx={idx}")
            return
        self.model_in = widget.model_out
        self._log.info(f"БЕРЁМ ИЗ {widget.name}")

    def set_to_model(self, idx: int | None = None):
        if idx is None:
            idx = self.cbxTo.currentIndex()
        widget = self._get_model_current_widget(self.cbxTo, idx)
        if widget is None:
            self._log.warning(f"Не выбран приёмник: idx={idx}")
            return
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
            if isinstance(device, (CameraWidget, ScannerWidget)):
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
        self, device_widgets: dict[int, CameraWidget | PrinterWidget | ScannerWidget]
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

    def start(self, toggled: bool) -> None:
        """Toggle run state and refresh the transport icon."""
        self._setup_icon(toggled)
        self.run(toggled)

    def set_interval_settings(self, value: int) -> None:
        """Handle interval UI change; delay is read dynamically in ``send_data``."""
        del value

    def send_data(self) -> None:
        """Transfer the first ready code from source to destination (FIFO)."""
        if self.model_in is None or self.model_out is None:
            self._log.warning(
                f"Не заданы источники: IN:{self.model_in} OUT:{self.model_out}"
            )
            return
        if not self.model_in.rowCount():
            return
        item = self.model_in.item(0, 0)
        if item is None:
            return
        interval_ms = self.spInterval.value()
        now = time.monotonic()
        if self._last_transferred_at is not None:
            elapsed_ms = (now - self._last_transferred_at) * 1000.0
            if elapsed_ms < interval_ms:
                return
        if not is_item_ready(item, interval_ms):
            return
        row = self.model_in.takeRow(0)
        code = get_clean_code(row[0].text())
        self.model_out.appendRow(create_code_item(code))
        self._last_transferred_at = now

    def run(self, toggled: bool) -> None:
        """Start or stop per-code transfer polling."""
        if toggled:
            self._log.info(f"ТРАНСПОРТ СТАРТ")
            self.set_from_model()
            self.set_to_model()
            self._code_scheduler.start(self.send_data)
        else:
            self._log.info(f"ТРАНСПОРТ ОСТАНОВКА")
            self._code_scheduler.stop()
            self._last_transferred_at = None
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
