from PySide6.QtCore import Signal, QObject, QTimer

from core.printing.printer_core import PrinterEmul


class PrinterProxy(QObject):
    buffer_size = Signal(int)
    buffer_data = Signal(list)

    def __init__(self):
        super().__init__()
        self._printer: PrinterEmul | None = None
        self._data_update_timer = self._setup_timer()

    def _setup_timer(self) -> QTimer:
        timer = QTimer()
        timer.setInterval(500)
        # noinspection PyUnresolvedReferences
        timer.timeout.connect(self.check_size)
        # noinspection PyUnresolvedReferences
        timer.timeout.connect(self.check_data)
        return timer

    def start(self, name: str, port: int, buffer: int):
        self._printer = PrinterEmul(name, port, buffer)
        self._printer.start()
        self._data_update_timer.start()

    def stop(self):
        if self._printer is None:
            return
        self._printer.stop()
        self._data_update_timer.stop()
        self._printer = None

    def check_size(self):
        size = self._printer.buffer_size()
        # noinspection PyUnresolvedReferences
        self.buffer_size.emit(size)

    def set_buffer_size(self, size: int):
        if self._printer is None:
            return
        self._printer.set_buffer_size(size)

    def check_data(self):
        buffer_data = self._printer.buffer_data()
        # noinspection PyUnresolvedReferences
        self.buffer_data.emit(buffer_data)

    def remove(self, code: str):
        self._printer.remove(code)
