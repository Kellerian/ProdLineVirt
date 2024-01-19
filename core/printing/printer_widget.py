from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import QWidget
from core.printing.printer_proxy import PrinterProxy
from forms.Printer import Ui_Form
import qtawesome
from libs.model_processing import update_model_data


class PrinterWidget(QWidget, Ui_Form):

    def __init__(self, name: str, port: int):
        super().__init__()
        self.setupUi(self)
        self.PLAY_ICON = qtawesome.icon('fa5s.play', color="#00FF00")
        self.STOP_ICON = qtawesome.icon('fa.stop', color="#FF0000")

        self._setup_icon(self.tbRun.isChecked())
        self._model = QStandardItemModel()

        self.lstData.setModel(self._model)
        self.lstData.setDragEnabled(True)
        self._printer = self._get_printer_proxy()
        self._connect_ui()
        self._data_list: list[str] = []
        self.leName.setText(name)
        self.leConnetionStr.setText(str(port))

    def _connect_ui(self):
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.spAmount.valueChanged.connect(self._set_printer_buffer_size)
        self._model.rowsAboutToBeRemoved.connect(
            self._model_rows_to_be_removed
        )

    def _set_printer_buffer_size(self, value: int):
        self._printer.set_buffer_size(value)

    def _model_rows_to_be_removed(self, _, first: int, last: int):
        for i in range(first, last + 1):
            index = self._model.index(i, 0)
            item_text = self._model.data(index, Qt.ItemDataRole.DisplayRole)
            self._delete_item(item_text)

    def _delete_item(self, row_data: str):
        self._printer.remove(row_data)
        self._data_list.remove(row_data)

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setIcon(self.STOP_ICON)
        else:
            self.tbRun.setIcon(self.PLAY_ICON)

    def _get_printer_proxy(self) -> PrinterProxy:
        pp = PrinterProxy()
        pp.buffer_size.connect(self._set_buffer_size_info)
        pp.buffer_data.connect(self._populate_list_with_buffer_data)
        return pp

    def _set_buffer_size_info(self, buffer_size: int):
        self.lstData.setToolTip(f"БУФФЕР: {buffer_size}")

    def _populate_list_with_buffer_data(self, data: list[str]):
        if not data:
            return
        new_rows = [row for row in data if row not in self._data_list]
        if new_rows:
            self._data_list.extend(new_rows)
            update_model_data(self._model, self._data_list)

    def _clear_data(self):
        self._data_list.clear()
        self._model.clear()

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
