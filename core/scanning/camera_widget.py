import qtawesome
from PyQt6.QtCore import QStringListModel
from PyQt6.QtWidgets import QWidget

from core.scanning.camera_proxy import CameraProxy
from forms.Camera import Ui_Form


class CameraWidget(QWidget, Ui_Form):
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
        self._printer = self._get_camera_proxy()
        self._connect_ui()
        self._data_list: list[str] = []

    def _connect_ui(self):
        self.tbRun.toggled.connect(self._run_action)
        self.tbRun.toggled.connect(self._setup_icon)
        self.tbDel.clicked.connect(self._pop_code)

    def _pop_code(self):
        pass

    def _get_camera_proxy(self) -> CameraProxy:
        cp = CameraProxy()
        return cp

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setIcon(self.STOP_ICON)
        else:
            self.tbRun.setIcon(self.PLAY_ICON)

    def _clear_data(self):
        self._model.setStringList([])

    def _run_action(self, toggled: bool):
        pass
