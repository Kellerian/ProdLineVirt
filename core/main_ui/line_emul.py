from PyQt6.QtWidgets import QMainWindow
from core.printing.print_widget import PrinterWidget
from forms.Main import Ui_MainWindow


class MainLineField(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._w_prn = PrinterWidget()
        self.centralwidget.layout().addWidget(self._w_prn)

