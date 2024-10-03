from PySide6.QtCore import Signal, QObject, QTimer
from core.scanning.camera_core import CameraEmul


class CameraProxy(QObject):
    scanned = Signal(list)

    def __init__(self):
        super().__init__()
        self._camera: CameraEmul | None = None
        self._t_sent = self._get_timer()
        self._t_sent.timeout.connect(self._get_scanned_data)

    @staticmethod
    def _get_timer() -> QTimer:
        timer = QTimer()
        timer.setInterval(250)
        return timer

    def start(self, name: str, port: int):
        self._camera = CameraEmul(name, port)
        self._camera.start()
        self._t_sent.start()

    def stop(self):
        if self._camera is None:
            return
        self._camera.stop()
        self._t_sent.stop()
        self._camera = None

    def set_noread(self, enabled: bool, error_percent: int = 0):
        if self._camera is None:
            return
        self._camera.set_noread(enabled, error_percent)

    def set_grade(self, enabled: bool, error_percent: int = 0):
        if self._camera is None:
            return
        self._camera.set_grade(enabled, error_percent)

    def set_duplicates(self, enabled: bool, error_percent: int = 0):
        if self._camera is None:
            return
        self._camera.set_duplicates(enabled, error_percent)

    def send_data(self, messages: list[str]):
        if self._camera is None:
            return
        self._camera.send(messages)

    def _get_scanned_data(self):
        sent_data = self._camera.get_sent_data()
        self.scanned.emit(sent_data)
