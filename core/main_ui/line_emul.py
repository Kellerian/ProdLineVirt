from PyQt6.QtWidgets import QMainWindow
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from forms.Main import Ui_MainWindow


class MainLineField(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._s_prn = PrinterWidget()
        self._s_prn.leName.setText("DM.PRINT.LOCAL")
        self._s_prn.leConnetionStr.setText("9101")
        self.centralwidget.layout().addWidget(self._s_prn)
        self._s_cam = CameraWidget()
        self._s_cam.leName.setText("DM.CAM.LOCAL")
        self._s_cam.leConnetionStr.setText("23")
        self.centralwidget.layout().addWidget(self._s_cam)

        self._a1_cam = CameraWidget()
        self._a1_cam.leName.setText("AGR1.CAM.LOCAL")
        self._a1_cam.leConnetionStr.setText("27")
        self.centralwidget.layout().addWidget(self._a1_cam)
        self._a2_cam = CameraWidget()
        self._a2_cam.leName.setText("AGR2.CAM.LOCAL")
        self._a2_cam.leConnetionStr.setText("28")
        self.centralwidget.layout().addWidget(self._a2_cam)
        self._a3_cam = CameraWidget()
        self._a3_cam.leName.setText("AGR3.CAM.LOCAL")
        self._a3_cam.leConnetionStr.setText("29")
        self.centralwidget.layout().addWidget(self._a3_cam)
        self._a1_prn = PrinterWidget()
        self._a1_prn.leName.setText("AGR1.PRINT.LOCAL")
        self._a1_prn.leConnetionStr.setText("9102")
        self.centralwidget.layout().addWidget(self._a1_prn)

        self._v1_cam = CameraWidget()
        self._v1_cam.leName.setText("VER.CAM.LOCAL")
        self._v1_cam.leConnetionStr.setText("32")
        self.centralwidget.layout().addWidget(self._v1_cam)

    def closeEvent(self, a0):
        self._s_prn.run(False)
        self._s_cam.run(False)
        self._a1_prn.run(False)
        self._a1_cam.run(False)
        self._v1_cam.run(False)
