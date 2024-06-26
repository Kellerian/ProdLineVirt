from pathlib import Path
from typing import Iterator
from PySide6.QtWidgets import QFileDialog, QMainWindow
from core.main_ui.data import ConfigFile
from core.main_ui.flow_layout import FlowLayout
from core.printing.data import PrinterConfig
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.scanning.data import CameraConfig
from core.transporting.data import TransporterConfig
from core.transporting.transporter_widget import TransporterWidget
from forms.Main import Ui_MainWindow


class MainLineField(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._app_title = "Эмулятор производственной линии"
        self._device_widgets: dict[int, CameraWidget | PrinterWidget] = {}
        self._transporter_widgets: dict[int, TransporterWidget] = {}
        self.cam_port = self.cam_port_generator()
        self.printer_port = self.printer_port_generator()
        self._devices_layout = FlowLayout(self.scaDevices)
        self.scaDevices.setLayout(self._devices_layout)
        self.setup_connections()
        self._active_file: Path | None = None

    def update_title(self):
        if self._active_file is not None:
            self.setWindowTitle(f"{self._app_title} {self._active_file}")
        else:
            self.setWindowTitle(self._app_title)

    @staticmethod
    def cam_port_generator() -> Iterator[int]:
        cam_port = 23
        while cam_port < 9100:
            yield cam_port
            cam_port += 1

    @staticmethod
    def printer_port_generator() -> Iterator[int]:
        printer_port = 9101
        while printer_port < 21100:
            yield printer_port
            printer_port += 1

    def setup_connections(self):
        self.acAddPrinter.triggered.connect(self._ac_add_printer)
        self.acAddCamera.triggered.connect(self._ac_add_camera)
        self.acAddTransporter.triggered.connect(self.add_transporter)
        self.acOpen.triggered.connect(self.open_config)
        self.acSave.triggered.connect(self.save_config)
        self.acSaveAs.triggered.connect(self.save_config_as)
        self.acClose.triggered.connect(self.close)

    def _ac_add_printer(self):
        port = next(self.printer_port)
        name = f"PRN_{port}"
        self.add_printer(name, port)

    def add_printer(
        self, name: str, port: int, buffer: int = 1
    ) -> PrinterWidget:
        prn_w = PrinterWidget(name, port, buffer)
        self._add_device(prn_w)
        return prn_w

    def _ac_add_camera(self):
        port = next(self.cam_port)
        name = f"CAM_{port}"
        self.add_camera(name, port)

    def add_camera(self, name: str, port: int):
        cam_w = CameraWidget(name, port)
        self._add_device(cam_w)
        return cam_w

    def add_transporter(self) -> TransporterWidget:
        transport = TransporterWidget()
        transport.setup_models(self._device_widgets)
        self._add_transport(transport)
        return transport

    def save_config(self):
        if self._active_file is None:
            self.save_config_as()
            return
        self.save_configuration_to_file(self._active_file)

    def save_config_as(self):
        file_data = QFileDialog.getSaveFileName(
            self, "Укажите файл для сохранения конфигурации",
            filter="Файл настроек (*.json)"
        )
        if not file_data or not file_data[0]:
            return
        file_path = Path(file_data[0])
        self.save_configuration_to_file(file_path)
        self._active_file = file_path
        self.update_title()

    def save_configuration_to_file(self, file_path: Path):
        current_config = ConfigFile(
            printers=[
                dev.options() for dev in self._device_widgets.values()
                if isinstance(dev, PrinterWidget)
            ],
            cameras=[
                dev.options() for dev in self._device_widgets.values()
                if isinstance(dev, CameraWidget)
            ],
            transporters=[
                dev.options() for dev in self._transporter_widgets.values()
            ]
        )
        json_data = current_config.model_dump_json(indent=4)
        with open(file_path, 'w') as f:
            f.write(json_data)

    def _load_printers(
        self, printers: list[PrinterConfig], devices: dict[str, int]
    ):
        for prn in printers:
            prn_w = self.add_printer(prn.name, prn.port, prn.buffer)
            devices[prn_w.name] = id(prn_w)

    def _load_cameras(
        self, cameras: list[CameraConfig], devices: dict[str, int]
    ):
        for cam in cameras:
            cam_w = self.add_camera(cam.name, cam.port)
            cam_w.load_options(cam.config)
            devices[cam_w.name] = id(cam_w)

    def _load_transporters(
        self, transporters:  list[TransporterConfig], devices: dict[str, int]
    ):
        for trn in transporters:
            from_id = devices.get(trn.take_from)
            to_id = devices.get(trn.give_to)
            if from_id is None or to_id is None:
                continue
            trn_w = self.add_transporter()
            trn_w.set_source_ids(from_id, to_id)
            trn_w.set_interval(trn.interval)

    def process_config(self, config: ConfigFile):
        devices: dict[str, int] = {}
        self._load_printers(config.printers, devices)
        self._load_cameras(config.cameras, devices)
        self._load_transporters(config.transporters, devices)

    def open_config(self):
        file_data = QFileDialog.getOpenFileName(
            self, caption="Выберите файл настроек *.json",
            filter="Файл настроек (*.json)"
        )
        if not file_data or not file_data[0]:
            return
        file_path = Path(file_data[0])

        with open(file_path, 'r') as f:
            cfg_file = f.read()
        cfg = ConfigFile.model_validate_json(cfg_file)
        self.process_config(cfg)
        self._active_file = file_path
        self.update_title()

    def _add_transport(self, transport: TransporterWidget):
        self._transporter_widgets[id(transport)] = transport
        self.transporters_layout.addWidget(transport)

    def _add_device(self, device: CameraWidget | PrinterWidget):
        self._device_widgets[id(device)] = device
        self._devices_layout.addWidget(device)
        for twd in self._transporter_widgets.values():
            twd.setup_models(self._device_widgets)

    def closeEvent(self, a0):
        for twd in self._transporter_widgets.values():
            twd.run(False)
        for dwd in self._device_widgets.values():
            dwd.run(False)
