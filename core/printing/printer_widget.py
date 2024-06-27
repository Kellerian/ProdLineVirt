from logging import getLogger

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QLabel, QListView, QWidget

from core.printing.data import PrinterConfig
from core.printing.printer_proxy import PrinterProxy
from forms.Printer import Ui_Form
from libs.datamatrix import get_gs1dm_pixmap
from libs.loggers import UI_LOGGER
from libs.model_processing import update_model_data


class PrinterWidget(QWidget, Ui_Form):

    def __init__(self, name: str, port: int, buffer: int = 1):
        super().__init__()
        self.setupUi(self)
        self.name = name
        self._data_list: list[str] = []
        self._setup_icon(self.tbRun.isChecked())
        self.model_out = QStandardItemModel()
        self._log = getLogger(UI_LOGGER)
        self.lstData.setModel(self.model_out)
        self.lstData.setDragEnabled(True)
        self._printer = self._get_printer_proxy()
        self._connect_ui()
        self.leName.setText(name)
        self.leConnetionStr.setText(str(port))
        self.spAmount.setValue(buffer)
        self._lbl: QLabel | None = None

    def _connect_ui(self):
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.spAmount.valueChanged.connect(self._set_printer_buffer_size)
        self.model_out.rowsAboutToBeRemoved.connect(
            self._model_rows_to_be_removed
        )
        self.lstData.doubleClicked.connect(self.create_image)

    def _set_printer_buffer_size(self, value: int):
        self._printer.set_buffer_size(value)
        self._log.debug(f"BUFFER CHANGE: {value}")

    def _model_rows_to_be_removed(self, _: QModelIndex, first: int, last: int):
        self._log.debug(f"ROWS TO BE REMOVED from {first} to {last}")
        for i in range(first, last + 1):
            index = self.model_out.index(i, 0)
            item_text = self.model_out.data(index, Qt.ItemDataRole.DisplayRole)
            self._log.debug(f"REMOVE ROWS: {first} {last} {item_text}")
            self._delete_item(item_text)

    def _delete_item(self, row_data: str):
        try:
            self._printer.remove(row_data)
        except ValueError:
            pass
        try:
            self._data_list.remove(row_data)
        except ValueError:
            pass

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def _get_printer_proxy(self) -> PrinterProxy:
        pp = PrinterProxy()
        pp.buffer_size.connect(self._set_buffer_size_info)
        pp.buffer_data.connect(self._populate_list_with_buffer_data)
        return pp

    def _set_buffer_size_info(self, buffer_size: int):
        self.lstData.setToolTip(f"БУФФЕР: {buffer_size}")

    def _populate_list_with_buffer_data(self, data: list[str]):
        if data == self._data_list:
            return
        self._data_list = data
        update_model_data(self.model_out, self._data_list)

    def _clear_data(self):
        self._data_list.clear()
        self.model_out.clear()

    def run(self, toggled: bool):
        if not self.leName.text() and not self.leConnetionStr.text():
            self.tbRun.setChecked(False)
            return
        self.leName.setDisabled(toggled)
        self.leConnetionStr.setDisabled(toggled)
        if toggled:
            name = self.leName.text()
            buffer_size = self.spAmount.value()
            try:
                port = int(self.leConnetionStr.text())
            except ValueError:
                return
            self._printer.start(name, port, buffer_size)
            self._printer.set_buffer_size(self.spAmount.value())
        else:
            self._printer.stop()
            self._clear_data()

    def options(self) -> PrinterConfig:
        return PrinterConfig(
            name=self.name,
            port=int(self.leConnetionStr.text()),
            buffer=self.spAmount.value()
        )

    def create_image(self, idx: QModelIndex):
        sender: QListView = self.sender()
        model = sender.model()
        data = model.data(idx, Qt.ItemDataRole.DisplayRole)
        pix = get_gs1dm_pixmap(data)
        self._lbl = QLabel()
        self._lbl.setPixmap(pix)
        self._lbl.show()
