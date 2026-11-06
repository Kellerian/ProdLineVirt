"""Qt widget for the Line Emulator Modbus controller device."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QHeaderView, QMessageBox, QTableWidgetItem, QWidget

from core.controller.data import ControllerConfig, ControllerMode, ControllerType
from core.controller.runtime import ControllerRuntime
from forms.Controller import Ui_Form
from libs.loggers import CONTROLLER_LOGGER

logger = logging.getLogger(CONTROLLER_LOGGER)

_REGISTER_POLL_INTERVAL_MS = 500

_MODE_BY_COMBO_INDEX: tuple[ControllerMode, ...] = (
    ControllerMode.simplex,
    ControllerMode.duplex,
)

_TYPE_BY_COMBO_INDEX: tuple[ControllerType, ...] = (
    ControllerType.delta,
    ControllerType.xinje,
)


class ControllerWidget(QWidget, Ui_Form):
    """Виджет эмулятора контроллера (Doypack / Modbus) на холсте Line Emulator."""

    delete_requested = Signal()

    def __init__(
        self,
        name: str,
        port: int,
        queue_size: int = 10,
        mode: ControllerMode = ControllerMode.simplex,
        controller_type: ControllerType = ControllerType.delta,
        *,
        register_addresses: Sequence[int] | None = None,
    ) -> None:
        super().__init__()
        self.setupUi(self)
        self._setup_registers_table()
        self.name = name
        self._runtime: ControllerRuntime | None = None
        self._register_poll_timer = QTimer(self)
        self._register_poll_timer.setInterval(_REGISTER_POLL_INTERVAL_MS)
        self._register_poll_timer.timeout.connect(self._poll_register_values)
        self._setup_icon(self.tbRun.isChecked())
        self._connect_ui()
        self.leName.setText(name)
        self.lePort.setText(str(port))
        self.spQueueSize.setValue(queue_size)
        self._set_mode_combo(mode)
        self._set_type_combo(controller_type)
        if register_addresses is not None:
            self._fill_register_rows_from_addresses(register_addresses)

    def _setup_registers_table(self) -> None:
        """Настраивает колонки таблицы holding-регистров."""
        header = self.tblRegisters.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def load_options(self, config: ControllerConfig) -> None:
        """Apply saved JSON configuration to the widget fields.

        Args:
            config: Values loaded from ``ConfigFile.controllers``.
        """
        self.name = config.name
        self.leName.setText(config.name)
        self.lePort.setText(str(config.port))
        self.spQueueSize.setValue(config.queue_size)
        self._set_mode_combo(config.mode)
        self._set_type_combo(config.controller_type)
        self.tblRegisters.setRowCount(0)
        for addr in config.register_addresses:
            self._append_register_row(str(addr), value_text="")

    def _connect_ui(self) -> None:
        """Подключает сигналы элементов управления."""
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.tbDelete.clicked.connect(self._on_delete_clicked)
        self.btnAddRegister.clicked.connect(self._on_add_register_clicked)

    def _on_add_register_clicked(self) -> None:
        """Добавляет в таблицу пустую строку (адрес вводит пользователь)."""
        self._append_register_row("", value_text="")

    def _fill_register_rows_from_addresses(self, addresses: Sequence[int]) -> None:
        """Заполняет таблицу адресами (значения пустые)."""
        self.tblRegisters.setRowCount(0)
        for addr in addresses:
            self._append_register_row(str(addr), value_text="")

    def _append_register_row(self, address_text: str, *, value_text: str) -> None:
        """Добавляет строку: редактируемый адрес и колонку значения только для чтения."""
        row = self.tblRegisters.rowCount()
        self.tblRegisters.insertRow(row)
        flags_addr = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
        flags_val = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        addr_item = QTableWidgetItem(address_text)
        addr_item.setFlags(flags_addr)
        val_item = QTableWidgetItem(value_text)
        val_item.setFlags(flags_val)
        self.tblRegisters.setItem(row, 0, addr_item)
        self.tblRegisters.setItem(row, 1, val_item)

    def _set_value_cell_text(self, row: int, text: str) -> None:
        """Пишет текст в колонку «Значение», не меняя флаги существующего item."""
        item = self.tblRegisters.item(row, 1)
        if item is None:
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.tblRegisters.setItem(row, 1, item)
        item.setText(text)

    def _clear_value_column(self) -> None:
        """Очищает только колонку значений (адреса сохраняются)."""
        for row in range(self.tblRegisters.rowCount()):
            self._set_value_cell_text(row, "")

    def _start_register_poll(self) -> None:
        """Запускает периодический опрос holding и первый тик без ожидания интервала."""
        self._register_poll_timer.start(_REGISTER_POLL_INTERVAL_MS)
        self._poll_register_values()

    def _stop_register_poll(self) -> None:
        """Останавливает таймер опроса регистров."""
        self._register_poll_timer.stop()

    def _selected_mode(self) -> ControllerMode:
        """Возвращает режим линии по индексу ``cbMode``."""
        idx = self.cbMode.currentIndex()
        if 0 <= idx < len(_MODE_BY_COMBO_INDEX):
            return _MODE_BY_COMBO_INDEX[idx]
        return ControllerMode.simplex

    def _selected_type(self) -> ControllerType:
        """Возвращает тип ПЛК по индексу ``cbType``."""
        idx = self.cbType.currentIndex()
        if 0 <= idx < len(_TYPE_BY_COMBO_INDEX):
            return _TYPE_BY_COMBO_INDEX[idx]
        return ControllerType.delta

    def _set_mode_combo(self, mode: ControllerMode) -> None:
        """Устанавливает ``cbMode`` по значению ``ControllerMode``."""
        try:
            idx = _MODE_BY_COMBO_INDEX.index(mode)
        except ValueError:
            idx = 0
        self.cbMode.setCurrentIndex(idx)

    def _set_type_combo(self, controller_type: ControllerType) -> None:
        """Устанавливает ``cbType`` по значению ``ControllerType``."""
        try:
            idx = _TYPE_BY_COMBO_INDEX.index(controller_type)
        except ValueError:
            idx = 0
        self.cbType.setCurrentIndex(idx)

    def _set_fields_enabled(self, enabled: bool) -> None:
        """Включает или блокирует поля конфигурации."""
        self.leName.setEnabled(enabled)
        self.lePort.setEnabled(enabled)
        self.spQueueSize.setEnabled(enabled)
        self.cbMode.setEnabled(enabled)
        self.cbType.setEnabled(enabled)

    def _on_delete_clicked(self) -> None:
        """Запрашивает подтверждение удаления; эмитит сигнал, если виджет остановлен."""
        if self.tbRun.isChecked():
            QMessageBox.warning(
                self,
                "Удаление",
                "Остановите виджет перед удалением",
            )
            return
        name = self.leName.text().strip() or self.name
        reply = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить виджет «{name}»?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit()

    def _setup_icon(self, toggled: bool) -> None:
        """Переключает подпись и цвет кнопки запуска (R/S как у принтера)."""
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def _poll_register_values(self) -> None:
        """Считывает значения holding для строк с валидными адресами (только GUI-поток)."""
        if self._runtime is None or not self.tbRun.isChecked():
            return

        addrs: list[int] = []
        row_for_addr: list[int] = []
        for row in range(self.tblRegisters.rowCount()):
            item0 = self.tblRegisters.item(row, 0)
            raw = (item0.text() if item0 is not None else "").strip()
            if not raw:
                self._set_value_cell_text(row, "")
                continue
            try:
                addr = int(raw)
            except ValueError:
                self._set_value_cell_text(row, "")
                continue
            if addr < 0 or addr > 10_000:
                self._set_value_cell_text(row, "")
                continue
            addrs.append(addr)
            row_for_addr.append(row)

        try:
            values = self._runtime.read_holding_registers(addrs)
        except Exception as exc:
            logger.debug(
                "Controller widget: read_holding_registers raised: %s",
                exc,
            )
            return

        if len(values) != len(addrs):
            logger.debug(
                "Controller widget: read_holding_registers length mismatch "
                "(%s vs %s)",
                len(values),
                len(addrs),
            )
            return

        for row, val in zip(row_for_addr, values, strict=True):
            if isinstance(val, int):
                self._set_value_cell_text(row, str(val))
            else:
                self._set_value_cell_text(row, "")

    def run(self, toggled: bool) -> None:
        """Запускает или останавливает :class:`ControllerRuntime`."""
        if not self.leName.text() and not self.lePort.text():
            self.tbRun.setChecked(False)
            return

        if toggled:
            try:
                listen_port = int(self.lePort.text().strip())
            except ValueError:
                self.tbRun.setChecked(False)
                return

            queue_sz = self.spQueueSize.value()
            mode = self._selected_mode()
            ctrl_type = self._selected_type()
            duplex = mode == ControllerMode.duplex
            xinje = ctrl_type == ControllerType.xinje

            runtime = ControllerRuntime()
            try:
                runtime.start(
                    listen_port,
                    queue_sz,
                    duplex=duplex,
                    xinje=xinje,
                )
            except Exception:
                logger.error(
                    "Controller widget: failed to start runtime port=%s",
                    listen_port,
                    exc_info=True,
                )
                runtime.stop()
                self._runtime = None
                self._register_poll_timer.stop()
                self.tbRun.blockSignals(True)
                self.tbRun.setChecked(False)
                self.tbRun.blockSignals(False)
                self._setup_icon(False)
                self._set_fields_enabled(True)
                return

            self._runtime = runtime
            self._start_register_poll()

        self.name = self.leName.text().strip()

        if not toggled:
            self._stop_register_poll()
            if self._runtime is not None:
                self._runtime.stop()
            self._runtime = None
            self._clear_value_column()

        self._set_fields_enabled(not toggled)

    def options(self) -> ControllerConfig:
        """Собирает текущую конфигурацию для сохранения в JSON линии."""
        try:
            port = int(self.lePort.text().strip())
        except ValueError as exc:
            raise ValueError(
                "Порт карточки контроллера должен быть целым числом"
            ) from exc

        register_addresses: list[int] = []
        for row in range(self.tblRegisters.rowCount()):
            item = self.tblRegisters.item(row, 0)
            text = (item.text() if item is not None else "").strip()
            if not text:
                continue
            row_1based = row + 1
            try:
                addr = int(text)
            except ValueError as exc:
                raise ValueError(
                    f"Строка {row_1based}: адрес переменной должен быть целым числом"
                ) from exc
            if addr < 0 or addr > 10_000:
                raise ValueError(
                    f"Строка {row_1based}: адрес holding должен быть от 0 до 10000 "
                    "включительно"
                )
            register_addresses.append(addr)

        return ControllerConfig(
            name=self.leName.text().strip() or self.name,
            port=port,
            queue_size=self.spQueueSize.value(),
            mode=self._selected_mode(),
            controller_type=self._selected_type(),
            register_addresses=register_addresses,
        )
