"""Qt widget for the Line Emulator Modbus controller device."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from contextlib import contextmanager
from typing import Iterator

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QWidget,
)

from core.controller.addresses import parse_register_token
from core.controller.data import ControllerConfig, ControllerMode, ControllerType
from core.controller.runtime import ControllerRuntime
from forms.Controller import Ui_Form
from libs.loggers import CONTROLLER_LOGGER

logger = logging.getLogger(CONTROLLER_LOGGER)

_REGISTER_POLL_INTERVAL_MS = 500

_COLOR_VALUE_OK = QColor(0, 128, 0)
_COLOR_VALUE_ERROR = QColor(128, 0, 0)

_HOLDING_VALUE_MAX = 65_535

_VALUE_FLAGS_READ_ONLY = (
    Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
)
_VALUE_FLAGS_EDITABLE = _VALUE_FLAGS_READ_ONLY | Qt.ItemFlag.ItemIsEditable

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
        register_addresses: Sequence[str | int] | None = None,
    ) -> None:
        super().__init__()
        self.setupUi(self)
        self._setup_registers_table()
        self.name = name
        self._runtime: ControllerRuntime | None = None
        self._register_poll_timer = QTimer(self)
        self._register_poll_timer.setInterval(_REGISTER_POLL_INTERVAL_MS)
        self._register_poll_timer.timeout.connect(self._poll_register_values)
        self._register_cell_guard = 0
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
        """Настраивает колонки таблицы переменных (holding и coil)."""
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
            self._append_register_row(
                self._register_address_cell_text(addr),
                value_text="",
            )

    def _connect_ui(self) -> None:
        """Подключает сигналы элементов управления."""
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.tbDelete.clicked.connect(self._on_delete_clicked)
        self.btnAddRegister.clicked.connect(self._on_add_register_clicked)
        self.tblRegisters.itemChanged.connect(self._on_register_item_changed)

    def _on_add_register_clicked(self) -> None:
        """Добавляет в таблицу пустую строку (адрес вводит пользователь)."""
        self._append_register_row("", value_text="")

    def _register_address_cell_text(self, addr: str | int) -> str:
        """Текст ячейки «Переменная» для legacy ``int`` (не ``bool``) или строкового токена."""
        if type(addr) is int:
            return str(addr)
        return addr

    def _fill_register_rows_from_addresses(
        self,
        addresses: Sequence[str | int],
    ) -> None:
        """Заполняет таблицу адресами (значения пустые)."""
        self.tblRegisters.setRowCount(0)
        for addr in addresses:
            self._append_register_row(
                self._register_address_cell_text(addr),
                value_text="",
            )

    def _value_column_editable(self) -> bool:
        """``True``, если колонка «Значение» должна принимать правку с клавиатуры."""
        return self._runtime is not None and self.tbRun.isChecked()

    def _value_cell_flags(self) -> Qt.ItemFlag:
        """Флаги item колонки «Значение» в зависимости от состояния R/S."""
        if self._value_column_editable():
            return _VALUE_FLAGS_EDITABLE
        return _VALUE_FLAGS_READ_ONLY

    def _set_value_column_editable(self, editable: bool) -> None:
        """Включает или снимает ``ItemIsEditable`` у всех ячеек колонки «Значение»."""
        flags = _VALUE_FLAGS_EDITABLE if editable else _VALUE_FLAGS_READ_ONLY
        with self._register_cell_guard_ctx():
            for row in range(self.tblRegisters.rowCount()):
                item = self.tblRegisters.item(row, 1)
                if item is not None:
                    item.setFlags(flags)

    @contextmanager
    def _register_cell_guard_ctx(self) -> Iterator[None]:
        """Блокирует ``itemChanged`` на время программальной правки колонки «Значение»."""
        self._register_cell_guard += 1
        if self._register_cell_guard == 1:
            self.tblRegisters.blockSignals(True)
        try:
            yield
        finally:
            self._register_cell_guard -= 1
            if self._register_cell_guard == 0:
                self.tblRegisters.blockSignals(False)

    def _is_row_value_editor_open(self, row: int) -> bool:
        """``True``, если для строки открыт встроенный редактор колонки «Значение»."""
        if self.tblRegisters.state() != QAbstractItemView.State.EditingState:
            return False
        index = self.tblRegisters.currentIndex()
        if not index.isValid():
            return False
        return index.row() == row and index.column() == 1

    @staticmethod
    def _is_ascii_digit_text(text: str) -> bool:
        """Проверяет, что строка непуста и состоит только из ASCII-цифр ``0-9``."""
        if not text:
            return False
        return all("0" <= ch <= "9" for ch in text)

    def _parse_user_value_text(
        self,
        text: str,
        kind: str,
    ) -> tuple[int | bool | None, str | None]:
        """Разбирает ввод пользователя: ``(write_value, canonical)`` или ``(None, None)``."""
        stripped = text.strip()
        if not self._is_ascii_digit_text(stripped):
            return None, None
        number = int(stripped)
        if kind == "holding":
            if number < 0 or number > _HOLDING_VALUE_MAX:
                return None, None
            return number, str(number)
        if kind == "coil":
            coil_val = number > 0
            return coil_val, "True" if coil_val else "False"
        return None, None

    def _revert_value_cell_to_last_success(self, row: int) -> None:
        """Откатывает ячейку «Значение» к последнему успешному тексту из ``UserRole``."""
        with self._register_cell_guard_ctx():
            item = self._value_table_item(row)
            last = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(last, str) and last:
                item.setText(last)
                item.setForeground(_COLOR_VALUE_OK)
            else:
                item.setText("")
                item.setData(Qt.ItemDataRole.ForegroundRole, None)

    def _apply_successful_value_display(self, row: int, display_text: str) -> None:
        """Задаёт канонический текст, зелёный цвет и ``UserRole`` под защитой от ``itemChanged``."""
        with self._register_cell_guard_ctx():
            item = self._value_table_item(row)
            item.setText(display_text)
            item.setForeground(_COLOR_VALUE_OK)
            item.setData(Qt.ItemDataRole.UserRole, display_text)

    def _clear_polled_value_row(self, row: int, *, reset_user_role: bool) -> None:
        """Очищает ячейку «Значение» на тике опроса (пропуск при открытом редакторе)."""
        if self._is_row_value_editor_open(row):
            return
        with self._register_cell_guard_ctx():
            item = self._value_table_item(row)
            item.setText("")
            item.setData(Qt.ItemDataRole.ForegroundRole, None)
            if reset_user_role:
                item.setData(Qt.ItemDataRole.UserRole, None)

    def _append_register_row(self, address_text: str, *, value_text: str) -> None:
        """Добавляет строку: редактируемый адрес и колонку «Значение»."""
        row = self.tblRegisters.rowCount()
        self.tblRegisters.insertRow(row)
        flags_addr = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
        addr_item = QTableWidgetItem(address_text)
        addr_item.setFlags(flags_addr)
        val_item = QTableWidgetItem(value_text)
        val_item.setFlags(self._value_cell_flags())
        self.tblRegisters.setItem(row, 0, addr_item)
        self.tblRegisters.setItem(row, 1, val_item)

    def _value_table_item(self, row: int) -> QTableWidgetItem:
        """Возвращает item колонки «Значение», создавая при необходимости."""
        item = self.tblRegisters.item(row, 1)
        if item is None:
            item = QTableWidgetItem("")
            item.setFlags(self._value_cell_flags())
            self.tblRegisters.setItem(row, 1, item)
        return item

    def _clear_value_row(self, row: int) -> None:
        """Очищает текст, цвет и ``UserRole`` ячейки «Значение» (остановка карточки)."""
        with self._register_cell_guard_ctx():
            item = self._value_table_item(row)
            item.setText("")
            item.setData(Qt.ItemDataRole.ForegroundRole, None)
            item.setData(Qt.ItemDataRole.UserRole, None)

    def _clear_value_column(self) -> None:
        """Очищает колонку значений и снимает редактирование (адреса сохраняются)."""
        for row in range(self.tblRegisters.rowCount()):
            self._clear_value_row(row)
        self._set_value_column_editable(False)

    def _on_register_item_changed(self, item: QTableWidgetItem) -> None:
        """Коммит правки колонки «Значение»: разбор ввода и ``write_point``."""
        if self._register_cell_guard > 0:
            return
        if item.column() != 1:
            return
        if not self._value_column_editable():
            return

        row = item.row()
        addr_item = self.tblRegisters.item(row, 0)
        raw = (addr_item.text() if addr_item is not None else "").strip()
        if not raw:
            self._revert_value_cell_to_last_success(row)
            return
        try:
            parsed = parse_register_token(raw)
        except ValueError:
            self._revert_value_cell_to_last_success(row)
            return

        write_val, display = self._parse_user_value_text(item.text(), parsed.kind)
        if write_val is None or display is None:
            self._revert_value_cell_to_last_success(row)
            return

        runtime = self._runtime
        if runtime is None:
            return

        try:
            ok = runtime.write_point(parsed.kind, parsed.address, write_val)
        except Exception as exc:
            logger.debug(
                "Controller widget: write_point failed kind=%s address=%s: %s",
                parsed.kind,
                parsed.address,
                exc,
            )
            self._revert_value_cell_to_last_success(row)
            return

        if not ok:
            logger.debug(
                "Controller widget: write_point failed kind=%s address=%s",
                parsed.kind,
                parsed.address,
            )
            self._revert_value_cell_to_last_success(row)
            return

        self._apply_successful_value_display(row, display)

    def _start_register_poll(self) -> None:
        """Запускает опрос holding/coil через ``read_points`` и первый тик без ожидания интервала."""
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
        """Считывает holding/coil для валидных строк через ``read_points`` (GUI-поток)."""
        if self._runtime is None or not self.tbRun.isChecked():
            return

        points: list[tuple[str, int]] = []
        row_for_point: list[int] = []
        for row in range(self.tblRegisters.rowCount()):
            item0 = self.tblRegisters.item(row, 0)
            raw = (item0.text() if item0 is not None else "").strip()
            if not raw:
                self._clear_polled_value_row(row, reset_user_role=True)
                continue
            try:
                parsed = parse_register_token(raw)
            except ValueError:
                self._clear_polled_value_row(row, reset_user_role=True)
                continue
            points.append((parsed.kind, parsed.address))
            row_for_point.append(row)

        if not points:
            return

        try:
            values = self._runtime.read_points(points)
        except Exception as exc:
            logger.debug(
                "Controller widget: read_points raised: %s",
                exc,
            )
            return

        if len(values) != len(points):
            logger.debug(
                "Controller widget: read_points length mismatch "
                "(%s vs %s)",
                len(values),
                len(points),
            )
            return

        for row, val in zip(row_for_point, values, strict=True):
            if self._is_row_value_editor_open(row):
                continue
            if isinstance(val, bool):
                display = str(val)
                self._apply_successful_value_display(row, display)
            elif isinstance(val, int):
                display = str(val)
                self._apply_successful_value_display(row, display)
            else:
                with self._register_cell_guard_ctx():
                    item = self._value_table_item(row)
                    item.setText("")
                    item.setForeground(_COLOR_VALUE_ERROR)

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
            self._set_value_column_editable(True)
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

        register_addresses: list[str] = []
        for row in range(self.tblRegisters.rowCount()):
            item = self.tblRegisters.item(row, 0)
            text = (item.text() if item is not None else "").strip()
            if not text:
                continue
            row_1based = row + 1
            try:
                parsed = parse_register_token(text)
            except ValueError as exc:
                raise ValueError(
                    f"Строка {row_1based}: недопустимый адрес переменной"
                ) from exc
            register_addresses.append(parsed.token)

        return ControllerConfig(
            name=self.leName.text().strip() or self.name,
            port=port,
            queue_size=self.spQueueSize.value(),
            mode=self._selected_mode(),
            controller_type=self._selected_type(),
            register_addresses=register_addresses,
        )
