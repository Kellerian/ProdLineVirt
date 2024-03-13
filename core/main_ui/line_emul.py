from PyQt6.QtWidgets import QMainWindow
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from forms.Main import Ui_MainWindow


class MainLineField(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._device_widgets: list[CameraWidget | PrinterWidget] = []

    def setup_multicam_print(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))
        self._add(CameraWidget("AGR1.CAM.LOCAL", 27))
        self._add(CameraWidget("AGR2.CAM.LOCAL", 28))
        self._add(CameraWidget("AGR3.CAM.LOCAL", 29))
        self._add(CameraWidget("VER.CAM.LOCAL", 32))

    def setup_multiprint(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))
        self._add(PrinterWidget("AGR1.PRINT.LOCAL", 9102))
        self._add(PrinterWidget("AGR2.PRINT.LOCAL", 9103))
        self._add(CameraWidget("VER.CAM.LOCAL", 32))

    def setup_single_pack(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))
        self._add(PrinterWidget("AGR1.PRINT.LOCAL", 9102))
        self._add(CameraWidget("VER.CAM.LOCAL", 32))

    def two_cam_setup(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))
        self._add(CameraWidget("AGR.CAM.LOCAL", 27))
        self._add(CameraWidget("VER.CAM.LOCAL", 32))
        self._add(PrinterWidget("AGR.PRINT.LOCAL", 9102))

    def three_aggr_levels(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))
        self._add(PrinterWidget("AGR1.PRINT.LOCAL", 9102))
        self._add(PrinterWidget("AGR2.PRINT.LOCAL", 9103))
        self._add(PrinterWidget("AGR3.PRINT.LOCAL", 9104))
        self._add(PrinterWidget("AGR3.PRINT.LOCAL", 9105))


    def ser_aggr_cam(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))
        self._add(CameraWidget("AGR.CAM.LOCAL", 27))
        self._add(PrinterWidget("AGR1.PRINT.LOCAL", 9102))
        self._add(PrinterWidget("AGR2.PRINT.LOCAL", 9103))
        self._add(CameraWidget("VER.CAM.LOCAL", 32))

    def test_tandem(self):
        self._add(PrinterWidget("DM.PRINT.LOCAL", 9101))
        self._add(PrinterWidget("DM1.PRINT.LOCAL", 9102))
        self._add(CameraWidget("DM.CAM.LOCAL", 23))

    def _add(self, device: CameraWidget | PrinterWidget):
        self.centralwidget.layout().addWidget(device)
        self._device_widgets.append(device)

    def closeEvent(self, a0):
        for wd in self._device_widgets:
            wd.run(False)
