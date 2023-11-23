from PyQt6.QtCore import QObject

from core.scanning.camera_core import CameraEmul


class CameraProxy(QObject):
    def __init__(self):
        super().__init__()
        self._camera: CameraEmul | None = None

    def start(self, name: str, port: int, buffer: int):
        self._camera = CameraEmul(name, port, buffer)
        self._camera.start()

    def stop(self):
        self._camera.stop()
        self._camera = None
