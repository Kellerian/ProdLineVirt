from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from core.scanning.camera_core import CameraEmul


class CameraProxy(QObject):
    scanned = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._camera: CameraEmul | None = None
        self._t_sent = self._get_timer()
        # noinspection PyUnresolvedReferences
        self._t_sent.timeout.connect(self._get_scanned_data)

    @staticmethod
    def _get_timer() -> QTimer:
        timer = QTimer()
        timer.setInterval(250)
        return timer

    def start(self, name: str, port: int):
        self._camera = CameraEmul(name, port)
        self._camera.start()

    def stop(self):
        self._camera.stop()
        self._camera = None

    def set_noread(self, enabled: bool, error_percent: int = 0):
        self._camera.set_noread(enabled, error_percent)

    def set_grade(self, enabled: bool, error_percent: int = 0):
        self._camera.set_grade(enabled, error_percent)

    def set_duplicates(self, enabled: bool, error_percent: int = 0):
        self._camera.set_duplicates(enabled, error_percent)

    def send_data(self, messages: list[str]):
        self._camera.send(messages)

    def _get_scanned_data(self):
        sent_data = self._camera.get_sent_data()
        # noinspection PyUnresolvedReferences
        self.scanned.emit(sent_data)
