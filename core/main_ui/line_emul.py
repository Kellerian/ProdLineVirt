from pathlib import Path
from typing import Iterable, Iterator

from PySide6.QtWidgets import QFileDialog, QMainWindow, QWidget

from core.barcode_scanner.data import ScannerConfig
from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.data import GeneratorConfig
from core.generator.generator_widget import GeneratorWidget
from core.main_ui.data import ConfigFile
from core.main_ui.flow_layout import FlowLayout
from core.printing.data import PrinterConfig, PrinterLanguage
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.scanning.data import CameraConfig
from core.transporting.data import TransporterConfig
from core.transporting.transporter_widget import TransporterWidget
from forms.Main import Ui_MainWindow
from libs.media import get_icon


class MainLineField(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._app_title = "Эмулятор производственной линии"
        self.setWindowIcon(get_icon())
        self._device_widgets: dict[
            int, CameraWidget | PrinterWidget | ScannerWidget
        ] = {}
        self._transporter_widgets: dict[int, TransporterWidget] = {}
        self._generator_widgets: dict[int, GeneratorWidget] = {}
        self.cam_port = self.cam_port_generator()
        self.printer_port = self.printer_port_generator()
        self.scanner_name = self.scanner_name_generator()
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

    @staticmethod
    def scanner_name_generator(start: int = 1) -> Iterator[str]:
        """Yield default scanner widget names (SCAN_1, SCAN_2, ...).

        Args:
            start: First numeric suffix to emit.
        """
        index = start
        while True:
            yield f"SCAN_{index}"
            index += 1

    def _sync_scanner_name_generator(self) -> None:
        """Set default-name iterator past existing SCAN_N widgets."""
        max_index = 0
        for dev in self._device_widgets.values():
            if not isinstance(dev, ScannerWidget):
                continue
            name = dev.name
            if not name.startswith("SCAN_"):
                continue
            suffix = name[5:]
            if suffix.isdigit():
                max_index = max(max_index, int(suffix))
        self.scanner_name = self.scanner_name_generator(max_index + 1)

    def setup_connections(self):
        self.acAddPrinter.triggered.connect(self._ac_add_printer)
        self.acAddCamera.triggered.connect(self._ac_add_camera)
        self.acAddScanner.triggered.connect(self._ac_add_scanner)
        self.acAddTransporter.triggered.connect(self.add_transporter)
        self.acAddGenerator.triggered.connect(self.add_generator)
        self.acOpen.triggered.connect(self.open_config)
        self.acSave.triggered.connect(self.save_config)
        self.acSaveAs.triggered.connect(self.save_config_as)
        self.acClose.triggered.connect(self.close)
        self._setup_bulk_control_connections()

    def _setup_bulk_control_connections(self) -> None:
        """Connect bulk start/stop/clear menu actions."""
        self.acControlStartAll.triggered.connect(self._bulk_start_all)
        self.acControlStartPrinters.triggered.connect(self._bulk_start_printers)
        self.acControlStartCameras.triggered.connect(self._bulk_start_cameras)
        self.acControlStartScanners.triggered.connect(self._bulk_start_scanners)
        self.acControlStartTransporters.triggered.connect(
            self._bulk_start_transporters
        )
        self.acControlStartGenerators.triggered.connect(
            self._bulk_start_generators
        )
        self.acControlStopAll.triggered.connect(self._bulk_stop_all)
        self.acControlStopPrinters.triggered.connect(self._bulk_stop_printers)
        self.acControlStopCameras.triggered.connect(self._bulk_stop_cameras)
        self.acControlStopScanners.triggered.connect(self._bulk_stop_scanners)
        self.acControlStopTransporters.triggered.connect(
            self._bulk_stop_transporters
        )
        self.acControlStopGenerators.triggered.connect(
            self._bulk_stop_generators
        )
        self.acControlClearAll.triggered.connect(self._bulk_clear_all)
        self.acControlClearPrinters.triggered.connect(self._bulk_clear_printers)
        self.acControlClearCameras.triggered.connect(self._bulk_clear_cameras)
        self.acControlClearScanners.triggered.connect(self._bulk_clear_scanners)

    def _iter_printers(self) -> Iterator[PrinterWidget]:
        """Yield printer widgets in layout order."""
        for dev in self._device_widgets.values():
            if isinstance(dev, PrinterWidget):
                yield dev

    def _iter_cameras(self) -> Iterator[CameraWidget]:
        """Yield camera widgets in layout order."""
        for dev in self._device_widgets.values():
            if isinstance(dev, CameraWidget):
                yield dev

    def _iter_scanners(self) -> Iterator[ScannerWidget]:
        """Yield scanner widgets in layout order."""
        for dev in self._device_widgets.values():
            if isinstance(dev, ScannerWidget):
                yield dev

    def _iter_devices(
        self,
    ) -> Iterator[CameraWidget | PrinterWidget | ScannerWidget]:
        """Yield device widgets: printers, then cameras, then scanners."""
        yield from self._iter_printers()
        yield from self._iter_cameras()
        yield from self._iter_scanners()

    def _iter_transporters(self) -> Iterator[TransporterWidget]:
        """Yield transporter widgets."""
        yield from self._transporter_widgets.values()

    def _iter_generators(self) -> Iterator[GeneratorWidget]:
        """Yield generator widgets."""
        yield from self._generator_widgets.values()

    @staticmethod
    def _start_widgets(widgets: Iterable[QWidget]) -> None:
        """Start widgets whose Run toggle is currently off."""
        for widget in widgets:
            if not widget.tbRun.isChecked():
                widget.tbRun.setChecked(True)

    @staticmethod
    def _stop_widgets(widgets: Iterable[QWidget]) -> None:
        """Stop widgets whose Run toggle is currently on."""
        for widget in widgets:
            if widget.tbRun.isChecked():
                widget.tbRun.setChecked(False)

    @staticmethod
    def _clear_device_widgets(
        widgets: Iterable[CameraWidget | PrinterWidget | ScannerWidget],
    ) -> None:
        """Clear queue data on device widgets without stopping them."""
        for widget in widgets:
            widget.clear_data()

    def _bulk_start_all(self) -> None:
        """Start devices, then transporters, then generators."""
        self._start_widgets(self._iter_devices())
        self._start_widgets(self._iter_transporters())
        self._start_widgets(self._iter_generators())

    def _bulk_start_printers(self) -> None:
        self._start_widgets(self._iter_printers())

    def _bulk_start_cameras(self) -> None:
        self._start_widgets(self._iter_cameras())

    def _bulk_start_scanners(self) -> None:
        self._start_widgets(self._iter_scanners())

    def _bulk_start_transporters(self) -> None:
        self._start_widgets(self._iter_transporters())

    def _bulk_start_generators(self) -> None:
        self._start_widgets(self._iter_generators())

    def _bulk_stop_all(self) -> None:
        """Stop generators, then transporters, then devices."""
        self._stop_widgets(reversed(list(self._iter_generators())))
        self._stop_widgets(reversed(list(self._iter_transporters())))
        self._stop_widgets(reversed(list(self._iter_devices())))

    def _bulk_stop_printers(self) -> None:
        self._stop_widgets(self._iter_printers())

    def _bulk_stop_cameras(self) -> None:
        self._stop_widgets(self._iter_cameras())

    def _bulk_stop_scanners(self) -> None:
        self._stop_widgets(self._iter_scanners())

    def _bulk_stop_transporters(self) -> None:
        self._stop_widgets(self._iter_transporters())

    def _bulk_stop_generators(self) -> None:
        self._stop_widgets(self._iter_generators())

    def _bulk_clear_all(self) -> None:
        self._clear_device_widgets(self._iter_devices())

    def _bulk_clear_printers(self) -> None:
        self._clear_device_widgets(self._iter_printers())

    def _bulk_clear_cameras(self) -> None:
        self._clear_device_widgets(self._iter_cameras())

    def _bulk_clear_scanners(self) -> None:
        self._clear_device_widgets(self._iter_scanners())

    def _ac_add_printer(self):
        port = next(self.printer_port)
        name = f"PRN_{port}"
        self.add_printer(name, port)

    def add_printer(
        self,
        name: str,
        port: int,
        buffer: int = 1,
        language: PrinterLanguage = PrinterLanguage.legacy,
    ) -> PrinterWidget:
        prn_w = PrinterWidget(name, port, buffer, language)
        self._add_device(prn_w)
        return prn_w

    def _ac_add_camera(self):
        port = next(self.cam_port)
        name = f"CAM_{port}"
        self.add_camera(name, port)

    def add_camera(self, name: str, port: int) -> CameraWidget:
        cam_w = CameraWidget(name, port)
        self._add_device(cam_w)
        return cam_w

    def _ac_add_scanner(self) -> None:
        name = next(self.scanner_name)
        self.add_scanner(name)

    def add_scanner(
        self, name: str, port_name: str = ""
    ) -> ScannerWidget:
        """Add a barcode scanner widget to the line field.

        Args:
            name: Display name of the scanner device.
            port_name: Optional COM port to pre-select in the combo box.

        Returns:
            Created ``ScannerWidget`` instance.
        """
        scn_w = ScannerWidget(name, port_name)
        self._add_device(scn_w)
        return scn_w

    def add_transporter(self) -> TransporterWidget:
        transport = TransporterWidget()
        transport.setup_models(self._device_widgets)
        self._add_transport(transport)
        return transport

    def add_generator(self) -> GeneratorWidget:
        generator = GeneratorWidget()
        generator.setup_models(self._device_widgets)
        self._add_generator(generator)
        return generator

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
            scanners=[
                dev.options() for dev in self._device_widgets.values()
                if isinstance(dev, ScannerWidget)
            ],
            transporters=[
                dev.options() for dev in self._transporter_widgets.values()
            ],
            generators=[
                dev.options() for dev in self._generator_widgets.values()
            ]
        )
        json_data = current_config.model_dump_json(indent=4)
        with open(file_path, 'w') as f:
            f.write(json_data)

    def _load_printers(
        self, printers: list[PrinterConfig], devices: dict[str, int]
    ):
        for prn in printers:
            prn_w = self.add_printer(
                prn.name, prn.port, prn.buffer, prn.language
            )
            devices[prn_w.name] = id(prn_w)

    def _load_cameras(
        self, cameras: list[CameraConfig], devices: dict[str, int]
    ):
        for cam in cameras:
            cam_w = self.add_camera(cam.name, cam.port)
            cam_w.load_options(cam.config)
            devices[cam_w.name] = id(cam_w)

    def _load_scanners(
        self, scanners: list[ScannerConfig], devices: dict[str, int]
    ) -> None:
        """Restore scanner widgets from saved configuration."""
        for scn in scanners:
            scn_w = self.add_scanner(scn.name, scn.port_name)
            scn_w.load_options(scn.config)
            devices[scn_w.name] = id(scn_w)
        self._sync_scanner_name_generator()

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

    def _load_generator(
        self, generators: list[GeneratorConfig], devices: dict[str, int]
    ):
        for gen in generators:
            to_id = devices.get(gen.give_to)
            if to_id is None:
                continue
            gen_w = self.add_generator()
            gen_w.set_to_ids(to_id)
            gen_w.select_generator(gen.generator_type)
            gen_w.set_gtin(gen.gtin)
            gen_w.set_interval(gen.interval)

    def process_config(self, config: ConfigFile):
        devices: dict[str, int] = {}
        self._load_printers(config.printers, devices)
        self._load_cameras(config.cameras, devices)
        self._load_scanners(config.scanners, devices)
        self._load_transporters(config.transporters, devices)
        self._load_generator(config.generators, devices)

    def clear_ui(self) -> None:
        """Stop and delete all device, transporter, and generator widgets."""
        for key in self._device_widgets.copy():
            dev = self._device_widgets.pop(key)
            dev.setParent(None)
            dev.run(False)
            dev.deleteLater()
        for key in self._transporter_widgets.copy():
            trn = self._transporter_widgets.pop(key)
            trn.setParent(None)
            trn.run(False)
            trn.deleteLater()
        for key in self._generator_widgets.copy():
            gen = self._generator_widgets.pop(key)
            gen.setParent(None)
            gen.run(False)
            gen.deleteLater()
        self._sync_scanner_name_generator()

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
        self.clear_ui()
        self.process_config(cfg)
        self._active_file = file_path
        self.update_title()

    def _add_transport(self, transport: TransporterWidget) -> None:
        """Register a transporter, place it on the canvas, connect delete."""
        self._transporter_widgets[id(transport)] = transport
        self.transporters_layout.addWidget(transport)
        transport.delete_requested.connect(self._on_widget_delete_requested)

    def _add_generator(self, generator: GeneratorWidget) -> None:
        """Register a generator, place it on the canvas, connect delete."""
        self._generator_widgets[id(generator)] = generator
        self.transporters_layout.addWidget(generator)
        generator.delete_requested.connect(self._on_widget_delete_requested)

    def _add_device(
        self, device: CameraWidget | PrinterWidget | ScannerWidget
    ) -> None:
        """Register a device, place it on the canvas, refresh linked models."""
        self._device_widgets[id(device)] = device
        self._devices_layout.addWidget(device)
        device.delete_requested.connect(self._on_widget_delete_requested)
        for twd in self._transporter_widgets.values():
            twd.setup_models(self._device_widgets)
        for gwd in self._generator_widgets.values():
            gwd.setup_models(self._device_widgets)

    def _on_widget_delete_requested(self) -> None:
        """Route ``delete_requested`` from the signal sender to the remove API."""
        widget = self.sender()
        if isinstance(widget, (CameraWidget, PrinterWidget, ScannerWidget)):
            self._remove_device(widget)
        elif isinstance(widget, TransporterWidget):
            self._remove_transporter(widget)
        elif isinstance(widget, GeneratorWidget):
            self._remove_generator(widget)

    def _remove_device(
        self, device: CameraWidget | PrinterWidget | ScannerWidget
    ) -> None:
        """Remove a device from the registry and canvas; refresh linked models.

        Args:
            device: Device widget that requested deletion.
        """
        key = id(device)
        if key not in self._device_widgets:
            return
        self._device_widgets.pop(key)
        device.setParent(None)
        device.run(False)
        device.deleteLater()
        for twd in self._transporter_widgets.values():
            twd.setup_models(self._device_widgets)
        for gwd in self._generator_widgets.values():
            gwd.setup_models(self._device_widgets)
        if isinstance(device, ScannerWidget):
            self._sync_scanner_name_generator()

    def _remove_transporter(self, transport: TransporterWidget) -> None:
        """Remove a transporter from the registry and canvas.

        Args:
            transport: Transporter widget that requested deletion.
        """
        key = id(transport)
        if key not in self._transporter_widgets:
            return
        self._transporter_widgets.pop(key)
        transport.setParent(None)
        transport.run(False)
        transport.deleteLater()

    def _remove_generator(self, generator: GeneratorWidget) -> None:
        """Remove a generator from the registry and canvas.

        Args:
            generator: Generator widget that requested deletion.
        """
        key = id(generator)
        if key not in self._generator_widgets:
            return
        self._generator_widgets.pop(key)
        generator.setParent(None)
        generator.run(False)
        generator.deleteLater()

    def closeEvent(self, a0):
        for twd in self._transporter_widgets.values():
            twd.run(False)
        for gwd in self._generator_widgets.values():
            gwd.run(False)
        for dwd in self._device_widgets.values():
            dwd.run(False)
