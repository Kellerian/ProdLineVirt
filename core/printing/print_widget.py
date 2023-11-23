from PyQt6.QtCore import QStringListModel
from PyQt6.QtWidgets import QWidget
from core.printing.printer_proxy import PrinterProxy
from forms.Printer import Ui_Form
import qtawesome


class PrinterWidget(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.PLAY_ICON = qtawesome.icon('fa5s.play', color="#00FF00")
        self.STOP_ICON = qtawesome.icon('fa.stop', color="#FF0000")
        self.GARBAGE_ICON = qtawesome.icon(
            'ri.delete-bin-fill', color="#FF0000"
        )
        self._setup_icon(self.tbRun.isChecked())
        self.tbDel.setIcon(self.GARBAGE_ICON)
        self._model = QStringListModel()
        self.lstData.setModel(self._model)
        self.lstData.setDragEnabled(True)
        self._printer = self._get_printer_proxy()
        self._connect_ui()
        self._data_list: list[str] = []

    def _connect_ui(self):
        self.tbRun.toggled.connect(self._run_action)
        self.tbRun.toggled.connect(self._setup_icon)
        self.tbDel.clicked.connect(self._pop_code)

    def _pop_code(self):
        selected_rows = self.lstData.selectedIndexes()
        if not selected_rows:
            return
        for item_index in selected_rows:
            row_data = item_index.data()
            self._delete_item(row_data)
        self._model.setStringList(self._data_list)

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
        self.lblBuffer.setText(f"МЕСТА В БУФФЕРЕ: {buffer_size}")

    def _populate_list_with_buffer_data(self, data: list[str]):
        if not data:
            return
        new_rows = [row for row in data if row not in self._data_list]
        if new_rows:
            self._data_list.extend(new_rows)
            self._model.setStringList(self._data_list)

    def _clear_data(self):
        self._model.setStringList([])

    def _run_action(self, toggled: bool):
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
        else:
            self._printer.stop()
            self._clear_data()
