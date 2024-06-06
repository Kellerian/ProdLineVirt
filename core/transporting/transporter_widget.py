from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QWidget
from forms.Transporter import Ui_Form


class TransporterWidget(QWidget, Ui_Form):
    def __init__(
        self, model_in: QStandardItemModel, model_out: QStandardItemModel
    ):
        super().__init__()
        self.setupUi(self)
        self._setup_icon(self.tbRun.isChecked())
        self._timer_sender = QTimer()
        self._timer_sender.setInterval(self.spInterval.value())
        self._connect_ui()
        self.model_in = model_in
        self.model_out = model_out

    def _setup_icon(self, toggled: bool):
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def _connect_ui(self):
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.spInterval.valueChanged.connect(self.set_interval_settings)
        # noinspection PyUnresolvedReferences
        self._timer_sender.timeout.connect(self.send_data)

    def start(self, toggled: bool):
        self._setup_icon(toggled)
        self.run(toggled)

    def set_interval_settings(self, value: int):
        self._timer_sender.setInterval(value)

    def send_data(self):
        if not self.model_in.rowCount():
            return
        row = self.model_in.takeRow(0)
        self.model_out.appendRow(row)

    def run(self, toggled: bool):
        self.cbxFrom.setDisabled(toggled)
        self.cbxTo.setDisabled(toggled)
        if toggled:
            self._timer_sender.start()
        else:
            self._timer_sender.stop()
