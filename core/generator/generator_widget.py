from logging import getLogger
from PySide6.QtCore import QTimer, Slot
from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QComboBox, QWidget

from core.generator.generators import get_new_code
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.generator.data import CodeType, GeneratorConfig
from forms.Generator import Ui_Form
from libs.loggers import UI_LOGGER
from libs.code_cleanup import get_clean_code


class GeneratorWidget(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._log = getLogger(UI_LOGGER)
        self.name = f"GW_{id(self)}"
        self._setup_icon(self.tbRun.isChecked())
        self._timer_sender = QTimer()
        self._device_data: dict[int, CameraWidget | PrinterWidget] = {}
        self.model_out: QStandardItemModel | None = None
        self.code_type: CodeType = CodeType.UKZ
        self.gtin: str = self.leGtin.text().strip()
        self._populate_code_type_selection()
        self._connect_ui()

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
        self.cbxCodeType.currentIndexChanged.connect(self.set_code_type)

    def _populate_code_type_selection(self):
        model = QStandardItemModel()
        for c in CodeType:
            model.appendRow(
                [QStandardItem(c.value), QStandardItem(c.name)]
            )
        self.cbxCodeType.setModel(model)
        self.cbxCodeType.setModelColumn(0)

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

    def set_to_model(self, idx: int | None = None):
        if idx is None:
            idx = self.cbxTo.currentIndex()
        widget = self._get_model_current_widget(self.cbxTo, idx)
        self.model_out = widget.model_in
        self._log.info(f"ПЕРЕДАЁМ В {widget.name}")

    def set_to_ids(self, take_to: int):
        self.set_cbx_current_value(self.cbxTo, str(take_to))

    def set_generator_type(self, generator_type: str):
        try:
            self.code_type = CodeType(generator_type)
        except ValueError:
            self.code_type = CodeType[generator_type]

    def set_gtin(self, gtin: str):
        self.gtin = gtin
        self.leGtin.setText(gtin)

    @Slot(int)
    def set_code_type(self, row: int):
        if row < 0:
            return
        model = self.cbxCodeType.model()
        idx = model.index(row, 0)
        code_type = model.data(idx, Qt.ItemDataRole.DisplayRole)
        self.set_generator_type(code_type)

    def select_generator(self, generator_name: str):
        self.set_cbx_current_value(self.cbxCodeType, generator_name)

    @staticmethod
    def set_cbx_current_value(cbx: QComboBox, value: str):
        model = cbx.model()
        set_row = 0
        for row in range(model.rowCount()):
            index = model.index(row, 1)
            data = model.data(index, Qt.ItemDataRole.DisplayRole)
            if data == value:
                set_row = row
                break
        cbx.setCurrentIndex(set_row)

    def get_data_models(self) -> QStandardItemModel:
        to_model = QStandardItemModel()
        for device in self._device_data.values():
            dev_name = device.name
            dev_id = id(device)
            to_model.appendRow(
                [QStandardItem(dev_name), QStandardItem(str(dev_id))]
            )
        return to_model

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
        to_model = self.get_data_models()
        self._set_cbx_model(self.cbxTo, to_model)

    def set_source_ids(self, give_to: int):
        self.set_cbx_current_value(self.cbxTo, str(give_to))

    def set_interval(self, value: int):
        self.spInterval.setValue(value)

    def start(self, toggled: bool):
        self.gtin = self.leGtin.text().strip()
        self._timer_sender.setInterval(self.spInterval.value())
        self._setup_icon(toggled)
        self.run(toggled)

    def set_interval_settings(self, value: int):
        self._timer_sender.setInterval(value)

    def send_data(self):
        _c = get_new_code(self.gtin, self.code_type)
        row = QStandardItem(get_clean_code(_c))
        self.model_out.appendRow(row)

    def run(self, toggled: bool):
        if toggled:
            self._log.info(f"ГЕНЕРАТОР СТАРТ")
            self.set_to_model()
            self._timer_sender.start()
        else:
            self._log.info(f"ГЕНЕРАТОР ОСТАНОВКА")
            self._timer_sender.stop()
        self.cbxTo.setDisabled(toggled)

    def options(self) -> GeneratorConfig:
        generator_type = self.code_type
        gtin = self.leGtin.text().strip()
        to_wd = self._get_model_current_widget(
            self.cbxTo, self.cbxTo.currentIndex()
        )
        return GeneratorConfig(
            generator_type=generator_type.name,
            gtin=gtin,
            give_to=to_wd.name,
            interval=self.spInterval.value()
        )
