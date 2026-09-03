import logging
from pathlib import Path
from typing import Iterable, Iterator

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QResizeEvent, QShowEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QWidget

from core.barcode_scanner.data import ScannerConfig
from core.barcode_scanner.scanner_widget import ScannerWidget
from core.generator.data import GeneratorConfig
from core.generator.generator_widget import GeneratorWidget
from core.main_ui.data import ConfigFile
from core.main_ui.canvas_area import CanvasDeviceArea
from core.main_ui.sidebar_layout import SidebarLayout
from core.main_ui.user_settings import UserSettings, load_user_settings, save_user_settings
from core.printing.data import PrinterConfig
from core.printing.printer_widget import PrinterWidget
from core.scanning.camera_widget import CameraWidget
from core.scanning.data import CameraConfig
from core.transporting.data import TransporterConfig
from core.transporting.transporter_widget import TransporterWidget
from forms.Main import Ui_MainWindow
from libs.loggers import UI_LOGGER
from libs.media import get_icon
from libs.qt_theme import ThemeMode, apply_theme

_logger = logging.getLogger(UI_LOGGER)


class MainLineField(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._app_title = "Эмулятор производственной линии"
        self.setWindowIcon(get_icon())
        self._device_widgets: dict[
            str, CameraWidget | PrinterWidget | ScannerWidget
        ] = {}
        self._transporter_widgets: dict[str, TransporterWidget] = {}
        self._generator_widgets: dict[str, GeneratorWidget] = {}
        self.cam_port = self.cam_port_generator()
        self.printer_port = self.printer_port_generator()
        self.scanner_name = self.scanner_name_generator()
        self._canvas_area = CanvasDeviceArea(self.scaDevices)
        self._devices_layout = self._canvas_area.flow_layout
        self._sidebar_layout = SidebarLayout(parent=self.scaTransporters)
        self.transporters_layout.addWidget(self._sidebar_layout)
        self._user_settings = load_user_settings()
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
        self.acResetLayout.triggered.connect(self._on_reset_layout)
        self._setup_theme_connections()
        self._setup_bulk_control_connections()

    def _setup_theme_connections(self) -> None:
        """Connect View menu theme actions and sync with user settings."""
        self.acThemeSystem.triggered.connect(
            lambda: self._on_theme_preference_changed(ThemeMode.SYSTEM)
        )
        self.acThemeLight.triggered.connect(
            lambda: self._on_theme_preference_changed(ThemeMode.LIGHT)
        )
        self.acThemeDark.triggered.connect(
            lambda: self._on_theme_preference_changed(ThemeMode.DARK)
        )
        self._sync_theme_menu_from_settings()

    def _sync_theme_menu_from_settings(self) -> None:
        """Update checkable theme menu actions from persisted preference."""
        preference = self._user_settings.theme_preference
        for action in (
            self.acThemeSystem,
            self.acThemeLight,
            self.acThemeDark,
        ):
            action.blockSignals(True)
        try:
            self.acThemeSystem.setChecked(preference == ThemeMode.SYSTEM.value)
            self.acThemeLight.setChecked(preference == ThemeMode.LIGHT.value)
            self.acThemeDark.setChecked(preference == ThemeMode.DARK.value)
        finally:
            for action in (
                self.acThemeSystem,
                self.acThemeLight,
                self.acThemeDark,
            ):
                action.blockSignals(False)

    def _on_theme_preference_changed(self, mode: ThemeMode) -> None:
        """Persist theme preference and re-apply global QSS.

        Args:
            mode: Selected theme preference from the View menu.
        """
        if self._user_settings.theme_preference == mode.value:
            return

        self._user_settings = UserSettings(theme_preference=mode.value)
        save_user_settings(self._user_settings)

        app = QApplication.instance()
        if app is not None:
            effective_mode = apply_theme(app, mode)
            _logger.info(
                "Theme preference set to %s (effective=%s)",
                mode.value,
                effective_mode,
            )
        else:
            _logger.warning(
                "Theme preference set to %s but QApplication is unavailable",
                mode.value,
            )

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
        """Yield printer widgets in canvas visual order."""
        for device_id in self.get_canvas_device_order():
            widget = self._device_widgets.get(device_id)
            if isinstance(widget, PrinterWidget):
                yield widget

    def _iter_cameras(self) -> Iterator[CameraWidget]:
        """Yield camera widgets in canvas visual order."""
        for device_id in self.get_canvas_device_order():
            widget = self._device_widgets.get(device_id)
            if isinstance(widget, CameraWidget):
                yield widget

    def _iter_scanners(self) -> Iterator[ScannerWidget]:
        """Yield scanner widgets in canvas visual order."""
        for device_id in self.get_canvas_device_order():
            widget = self._device_widgets.get(device_id)
            if isinstance(widget, ScannerWidget):
                yield widget

    def _iter_devices(
        self,
    ) -> Iterator[CameraWidget | PrinterWidget | ScannerWidget]:
        """Yield canvas device widgets in visual flow order."""
        for device_id in self.get_canvas_device_order():
            widget = self._device_widgets.get(device_id)
            if widget is not None:
                yield widget

    def _iter_transporters(self) -> Iterator[TransporterWidget]:
        """Yield transporter widgets in sidebar visual order."""
        for device_id in self.get_sidebar_device_order():
            widget = self._transporter_widgets.get(device_id)
            if widget is not None:
                yield widget

    def _iter_generators(self) -> Iterator[GeneratorWidget]:
        """Yield generator widgets in sidebar visual order."""
        for device_id in self.get_sidebar_device_order():
            widget = self._generator_widgets.get(device_id)
            if widget is not None:
                yield widget

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
        device_id: str | None = None,
    ) -> PrinterWidget:
        prn_w = PrinterWidget(name, port, buffer, device_id=device_id)
        self._add_device(prn_w)
        return prn_w

    def _ac_add_camera(self):
        port = next(self.cam_port)
        name = f"CAM_{port}"
        self.add_camera(name, port)

    def add_camera(
        self, name: str, port: int, device_id: str | None = None
    ) -> CameraWidget:
        cam_w = CameraWidget(name, port, device_id=device_id)
        self._add_device(cam_w)
        return cam_w

    def _ac_add_scanner(self) -> None:
        name = next(self.scanner_name)
        self.add_scanner(name)

    def add_scanner(
        self,
        name: str,
        port_name: str = "",
        device_id: str | None = None,
    ) -> ScannerWidget:
        """Add a barcode scanner widget to the line field.

        Args:
            name: Display name of the scanner device.
            port_name: Optional COM port to pre-select in the combo box.
            device_id: Stable identifier from saved config; generated when omitted.

        Returns:
            Created ``ScannerWidget`` instance.
        """
        scn_w = ScannerWidget(name, port_name, device_id=device_id)
        self._add_device(scn_w)
        return scn_w

    def add_transporter(
        self, device_id: str | None = None
    ) -> TransporterWidget:
        transport = TransporterWidget(device_id=device_id)
        transport.setup_models(self._device_widgets)
        self._add_transport(transport)
        return transport

    def add_generator(self, device_id: str | None = None) -> GeneratorWidget:
        generator = GeneratorWidget(device_id=device_id)
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

    def save_configuration_to_file(self, file_path: Path) -> None:
        """Persist project JSON including layout order and dock state.

        Args:
            file_path: Destination path for the configuration file.
        """
        current_config = ConfigFile(
            printers=[dev.options() for dev in self._iter_printers()],
            cameras=[dev.options() for dev in self._iter_cameras()],
            scanners=[dev.options() for dev in self._iter_scanners()],
            transporters=[dev.options() for dev in self._iter_transporters()],
            generators=[dev.options() for dev in self._iter_generators()],
            sidebar_order=self.get_sidebar_device_order(),
            canvas_order=self.get_canvas_device_order(),
            dock_state=self._encode_dock_state(),
        )
        json_data = current_config.model_dump_json(indent=4)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_data)

    @staticmethod
    def _resolve_device_ref(
        ref: str,
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
    ) -> CameraWidget | PrinterWidget | ScannerWidget | None:
        """Resolve a persisted device reference by ``device_id`` or legacy name."""
        if ref in by_id:
            return by_id[ref]
        return by_name.get(ref)

    def _load_printers(
        self,
        printers: list[PrinterConfig],
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
    ) -> None:
        for prn in printers:
            prn_w = self.add_printer(
                prn.name, prn.port, prn.buffer, device_id=prn.device_id
            )
            prn_w.set_advanced_expanded(prn.advanced_expanded)
            by_id[prn_w.device_id] = prn_w
            by_name[prn_w.name] = prn_w

    def _load_cameras(
        self,
        cameras: list[CameraConfig],
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
    ) -> None:
        for cam in cameras:
            cam_w = self.add_camera(cam.name, cam.port, device_id=cam.device_id)
            cam_w.load_options(cam.config)
            cam_w.set_advanced_expanded(cam.advanced_expanded)
            by_id[cam_w.device_id] = cam_w
            by_name[cam_w.name] = cam_w

    def _load_scanners(
        self,
        scanners: list[ScannerConfig],
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
    ) -> None:
        """Restore scanner widgets from saved configuration."""
        for scn in scanners:
            scn_w = self.add_scanner(
                scn.name, scn.port_name, device_id=scn.device_id
            )
            scn_w.load_options(scn.config)
            scn_w.set_advanced_expanded(scn.advanced_expanded)
            by_id[scn_w.device_id] = scn_w
            by_name[scn_w.name] = scn_w
        self._sync_scanner_name_generator()

    def _load_transporters(
        self,
        transporters: list[TransporterConfig],
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
    ) -> None:
        for trn in transporters:
            from_dev = self._resolve_device_ref(trn.take_from, by_id, by_name)
            to_dev = self._resolve_device_ref(trn.give_to, by_id, by_name)
            if from_dev is None or to_dev is None:
                continue
            trn_w = self.add_transporter(device_id=trn.device_id)
            trn_w.set_source_ids(from_dev.device_id, to_dev.device_id)
            trn_w.set_interval(trn.interval)
            trn_w.set_advanced_expanded(trn.advanced_expanded)

    def _load_generator(
        self,
        generators: list[GeneratorConfig],
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget],
    ) -> None:
        for gen in generators:
            to_dev = self._resolve_device_ref(gen.give_to, by_id, by_name)
            if to_dev is None:
                continue
            gen_w = self.add_generator(device_id=gen.device_id)
            gen_w.set_to_ids(to_dev.device_id)
            gen_w.select_generator(gen.generator_type)
            gen_w.set_gtin(gen.gtin)
            gen_w.set_interval(gen.interval)
            gen_w.set_advanced_expanded(gen.advanced_expanded)

    def process_config(self, config: ConfigFile) -> None:
        """Restore devices, visual order, advanced panels, and dock layout."""
        by_id: dict[str, CameraWidget | PrinterWidget | ScannerWidget] = {}
        by_name: dict[str, CameraWidget | PrinterWidget | ScannerWidget] = {}
        self._load_printers(config.printers, by_id, by_name)
        self._load_cameras(config.cameras, by_id, by_name)
        self._load_scanners(config.scanners, by_id, by_name)
        self._load_transporters(config.transporters, by_id, by_name)
        self._load_generator(config.generators, by_id, by_name)
        self._apply_device_layout(config.sidebar_order, config.canvas_order)
        self._restore_dock_state(config.dock_state)
        self._canvas_area.relayout()

    def showEvent(self, event: QShowEvent) -> None:
        """Reflow canvas cards once the main window has a valid geometry."""
        super().showEvent(event)
        self._canvas_area.relayout()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Keep wrapped canvas layout in sync with the central scroll area."""
        super().resizeEvent(event)
        self._canvas_area.relayout()

    def clear_ui(self) -> None:
        """Stop and delete all device, transporter, and generator widgets."""
        for device_id in self._device_widgets.copy():
            dev = self._device_widgets.pop(device_id)
            self._canvas_area.remove_widget(dev)
            dev.setParent(None)
            dev.run(False)
            dev.deleteLater()
        for device_id in self._transporter_widgets.copy():
            trn = self._transporter_widgets.pop(device_id)
            self._sidebar_layout.remove_widget(trn)
            trn.setParent(None)
            trn.run(False)
            trn.deleteLater()
        for device_id in self._generator_widgets.copy():
            gen = self._generator_widgets.pop(device_id)
            self._sidebar_layout.remove_widget(gen)
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
        """Register a transporter, place it on the sidebar, connect delete."""
        self._transporter_widgets[transport.device_id] = transport
        self._sidebar_layout.add_widget(transport)
        transport.delete_requested.connect(self._on_widget_delete_requested)

    def _add_generator(self, generator: GeneratorWidget) -> None:
        """Register a generator, place it on the sidebar, connect delete."""
        self._generator_widgets[generator.device_id] = generator
        self._sidebar_layout.add_widget(generator)
        generator.delete_requested.connect(self._on_widget_delete_requested)

    def _add_device(
        self, device: CameraWidget | PrinterWidget | ScannerWidget
    ) -> None:
        """Register a device, place it on the canvas, refresh linked models."""
        self._device_widgets[device.device_id] = device
        self._canvas_area.add_widget(device)
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
        key = device.device_id
        if key not in self._device_widgets:
            return
        self._device_widgets.pop(key)
        self._canvas_area.remove_widget(device)
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
        """Remove a transporter from the registry and sidebar.

        Args:
            transport: Transporter widget that requested deletion.
        """
        key = transport.device_id
        if key not in self._transporter_widgets:
            return
        self._transporter_widgets.pop(key)
        self._sidebar_layout.remove_widget(transport)
        transport.setParent(None)
        transport.run(False)
        transport.deleteLater()

    def _default_sidebar_order(self) -> list[str]:
        """Return default sidebar order: transporters then generators."""
        return [
            *self._transporter_widgets.keys(),
            *self._generator_widgets.keys(),
        ]

    def _default_canvas_order(self) -> list[str]:
        """Return default canvas order: printers, cameras, then scanners."""
        order: list[str] = []
        for device_id, widget in self._device_widgets.items():
            if isinstance(widget, PrinterWidget):
                order.append(device_id)
        for device_id, widget in self._device_widgets.items():
            if isinstance(widget, CameraWidget):
                order.append(device_id)
        for device_id, widget in self._device_widgets.items():
            if isinstance(widget, ScannerWidget):
                order.append(device_id)
        return order

    def _apply_device_layout(
        self,
        sidebar_order: list[str],
        canvas_order: list[str],
    ) -> None:
        """Apply saved device order or zone defaults when arrays are empty."""
        if sidebar_order:
            self.set_sidebar_device_order(sidebar_order)
        else:
            self.set_sidebar_device_order(self._default_sidebar_order())
        if canvas_order:
            self.set_canvas_device_order(canvas_order)
        else:
            self.set_canvas_device_order(self._default_canvas_order())

    def _apply_default_dock_layout(self) -> None:
        """Reset sidebar dock to the left area and ensure it is visible."""
        if self.dockSidebar.isFloating():
            self.dockSidebar.setFloating(False)
        self.removeDockWidget(self.dockSidebar)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockSidebar)
        self.dockSidebar.show()

    def _apply_default_layout(self) -> None:
        """Reset dock areas and device order to factory defaults."""
        self._apply_default_dock_layout()
        self.set_sidebar_device_order(self._default_sidebar_order())
        self.set_canvas_device_order(self._default_canvas_order())

    def _encode_dock_state(self) -> str:
        """Serialize main-window dock layout as a base64 string."""
        return bytes(self.saveState().toBase64()).decode("ascii")

    def _restore_dock_state(self, dock_state: str | None) -> None:
        """Restore dock layout from project JSON or apply defaults.

        Args:
            dock_state: Base64 ``QMainWindow.saveState`` payload, or ``None``.
        """
        if dock_state:
            restored = self.restoreState(
                QByteArray.fromBase64(dock_state.encode("ascii"))
            )
            if not restored:
                _logger.warning(
                    "Failed to restore dock state; applying default dock layout"
                )
                self._apply_default_dock_layout()
            return
        self._apply_default_dock_layout()

    def _on_reset_layout(self) -> None:
        """Menu handler: reset dock and device order without saving to disk."""
        self._apply_default_layout()

    def get_canvas_device_order(self) -> list[str]:
        """Return canvas ``device_id`` order for layout persistence (#9)."""
        return self._canvas_area.get_order()

    def set_canvas_device_order(self, device_ids: list[str]) -> None:
        """Apply saved canvas order by ``device_id`` (#9)."""
        self._canvas_area.set_order(device_ids)

    def get_sidebar_device_order(self) -> list[str]:
        """Return sidebar ``device_id`` order for layout persistence (#9)."""
        return self._sidebar_layout.get_order()

    def set_sidebar_device_order(self, device_ids: list[str]) -> None:
        """Apply saved sidebar order by ``device_id`` (#9)."""
        self._sidebar_layout.set_order(device_ids)

    def _remove_generator(self, generator: GeneratorWidget) -> None:
        """Remove a generator from the registry and sidebar.

        Args:
            generator: Generator widget that requested deletion.
        """
        key = generator.device_id
        if key not in self._generator_widgets:
            return
        self._generator_widgets.pop(key)
        self._sidebar_layout.remove_widget(generator)
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
