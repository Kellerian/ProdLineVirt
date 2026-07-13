"""Виджет эмулятора ручного сканера штрихкодов (COM, PySide6)."""

from __future__ import annotations

from logging import getLogger

import qtawesome as qta
from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QMessageBox, QWidget

from core.barcode_scanner.data import ScannerConfig, ScannerParams
from core.barcode_scanner.scanner_proxy import ScannerProxy
from forms.Scanner import Ui_Form
from libs.code_scheduler import CodeScheduler
from libs.loggers import UI_LOGGER
from libs.model_processing import (
    CustomItemModel,
    count_ready_prefix,
    create_code_item,
    stamp_item,
)
from libs.serial_port import (
    SerialPortConfig,
    SerialPortError,
    list_available_ports,
    open_serial_port,
)

_COM_PORT_PLACEHOLDER = "Выберите порт"
_SEND_BATCH_SIZE = 1
_SEND_INTERVAL_MS = 0


class ScannerWidget(QWidget, Ui_Form):
    """Виджет сканера: очередь кодов, COM-порт, ручная отправка и DnD."""

    delete_requested = Signal()

    def __init__(self, name: str, port_name: str = "") -> None:
        """Инициализирует виджет сканера.

        Args:
            name: Отображаемое имя устройства на линии.
            port_name: Имя COM-порта для предвыбора в combo (пусто — placeholder).
        """
        super().__init__()
        self.setupUi(self)
        self._setup_icon(self.tbRun.isChecked())
        self._setup_send_icon()
        self._setup_refresh_ports_icon()
        self.name = name
        self._params = ScannerParams()
        self._log = getLogger(UI_LOGGER)

        self.model_in = CustomItemModel()
        self.model_out = QStandardItemModel()

        self.lstData.setModel(self.model_in)
        self.lstData.setAcceptDrops(True)
        self.lstData.setDropIndicatorShown(True)

        self._scanner = self._get_scanner_proxy()
        self._scheduler = CodeScheduler()

        self.model_in.rowsInserted.connect(self._on_model_in_rows_inserted)
        self._connect_ui()

        self.leName.setText(name)
        self._refresh_com_ports(select_port=port_name or None)

    def _connect_ui(self) -> None:
        """Подключает сигналы элементов формы."""
        self.tbRun.toggled.connect(self.run)
        self.tbRun.toggled.connect(self._setup_icon)
        self.tbRefreshPorts.clicked.connect(self._on_refresh_ports_clicked)
        self.tbDelete.clicked.connect(self._on_delete_clicked)
        self.btnSend.clicked.connect(self._send_manual_input)
        self.leManualInput.returnPressed.connect(self._send_manual_input)

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

    def _setup_send_icon(self) -> None:
        """Задаёт иконку отправки на кнопке ручного ввода."""
        icon = qta.icon("fa5s.paper-plane", color="#FFFFFF")
        self.btnSend.setIcon(icon)
        self.btnSend.setText("")

    def _setup_refresh_ports_icon(self) -> None:
        """Задаёт иконку обновления списка COM-портов."""
        icon = qta.icon("fa5s.sync", color="#FFFFFF")
        self.tbRefreshPorts.setIcon(icon)
        self.tbRefreshPorts.setText("")

    def _on_refresh_ports_clicked(self) -> None:
        """Перечитывает доступные COM-порты, сохраняя текущий выбор."""
        current_port = self._get_port_name() or None
        self._refresh_com_ports(select_port=current_port)

    def _get_scanner_proxy(self) -> ScannerProxy:
        """Создаёт прокси сканера и подключает сигналы ядра."""
        proxy = ScannerProxy()
        proxy.scanned.connect(self._populate_scanned_data)
        proxy.open_failed.connect(self._on_scanner_open_failed)
        return proxy

    def _refresh_com_ports(self, select_port: str | None = None) -> None:
        """Заполняет combo доступными COM-портами, сохраняя placeholder.

        Args:
            select_port: Имя порта для выбора после обновления списка.
        """
        self.cbxComPort.blockSignals(True)
        self.cbxComPort.clear()
        self.cbxComPort.addItem(_COM_PORT_PLACEHOLDER)
        placeholder = self.cbxComPort.model().item(0)
        if placeholder is not None:
            placeholder.setEnabled(False)

        for port_name in list_available_ports():
            self.cbxComPort.addItem(port_name)

        if select_port:
            index = self.cbxComPort.findText(select_port)
            if index >= 0:
                self.cbxComPort.setCurrentIndex(index)
            else:
                self.cbxComPort.addItem(select_port)
                self.cbxComPort.setCurrentIndex(self.cbxComPort.count() - 1)
        else:
            self.cbxComPort.setCurrentIndex(0)

        self.cbxComPort.blockSignals(False)

    def _get_port_name(self) -> str:
        """Возвращает выбранное имя COM-порта или пустую строку."""
        if self.cbxComPort.currentIndex() <= 0:
            return ""
        return self.cbxComPort.currentText()

    def _send_manual_input(self) -> None:
        """Добавляет текст из поля ручного ввода в очередь отправки."""
        text = self.leManualInput.text().strip()
        if not text:
            return
        self.model_in.appendRow(create_code_item(text))
        self.leManualInput.clear()

    def send_data(self) -> None:
        """Отправляет готовый код из очереди в COM через прокси сканера."""
        self.lstData.setToolTip(
            f"Данных на отправку {self.model_in.rowCount()}"
        )
        if self.model_in.rowCount() < _SEND_BATCH_SIZE:
            return

        ready_count = count_ready_prefix(self.model_in, _SEND_INTERVAL_MS)
        if ready_count < _SEND_BATCH_SIZE:
            return

        data_to_send: list[str] = []
        for _ in range(_SEND_BATCH_SIZE):
            row = self.model_in.takeRow(0)
            item = row[0]
            data_to_send.append(item.text())
        self._scanner.send_data(data_to_send)

    def _on_model_in_rows_inserted(
        self, parent: QModelIndex, first: int, last: int
    ) -> None:
        """Проставляет метку времени элементам, попавшим в очередь (DnD и др.)."""
        del parent
        for row in range(first, last + 1):
            item = self.model_in.item(row, 0)
            if item is not None:
                stamp_item(item)

    def _populate_scanned_data(self, data: list[str]) -> None:
        """Добавляет успешно отправленные в COM коды в исходящую модель."""
        for row in data:
            self.model_out.appendRow(create_code_item(row))

    def _setup_icon(self, toggled: bool) -> None:
        """Обновляет внешний вид кнопки Run/Stop."""
        if toggled:
            self.tbRun.setText("S")
            self.tbRun.setStyleSheet("color: #FF0000")
        else:
            self.tbRun.setText("R")
            self.tbRun.setStyleSheet("color: #00FF00")

    def clear_data(self) -> None:
        """Очищает входную и исходящую очереди кодов без остановки эмулятора."""
        self.model_in.clear()
        self.model_out.clear()
        self._scanner.clear_queues()

    def _verify_port_available(self, config: SerialPortConfig) -> bool:
        """Проверяет доступность COM-порта перед запуском эмулятора.

        Args:
            config: Параметры порта для проверки.

        Returns:
            ``True``, если порт удалось открыть; иначе ``False`` и QMessageBox.
        """
        try:
            port = open_serial_port(config)
            port.close()
            return True
        except SerialPortError as exc:
            QMessageBox.warning(
                self,
                "Сканер",
                f"Не удалось открыть COM-порт {config.port_name}:\n{exc}",
            )
            return False

    def _on_scanner_open_failed(self, message: str) -> None:
        """Сбрасывает Run при ошибке открытия COM в фоновом потоке ядра."""
        port_name = self._get_port_name()
        self._scheduler.stop()
        self._scanner.stop()
        self.tbRun.blockSignals(True)
        self.tbRun.setChecked(False)
        self.tbRun.blockSignals(False)
        self.leName.setDisabled(False)
        self.cbxComPort.setDisabled(False)
        self.tbRefreshPorts.setDisabled(False)
        self._setup_icon(False)
        QMessageBox.warning(
            self,
            "Сканер",
            f"Не удалось открыть COM-порт {port_name}:\n{message}",
        )
        self._log.error(
            "[%s] Ошибка открытия COM-порта %s: %s",
            self.name,
            port_name,
            message,
        )

    def run(self, toggled: bool) -> None:
        """Запускает или останавливает эмулятор сканера."""
        if toggled:
            name = self.leName.text().strip()
            if not name:
                QMessageBox.warning(
                    self,
                    "Сканер",
                    "Введите название перед запуском.",
                )
                self.tbRun.blockSignals(True)
                self.tbRun.setChecked(False)
                self.tbRun.blockSignals(False)
                self._setup_icon(False)
                return

            port_name = self._get_port_name()
            if not port_name:
                QMessageBox.warning(
                    self,
                    "Сканер",
                    "Выберите COM-порт перед запуском.",
                )
                self.tbRun.blockSignals(True)
                self.tbRun.setChecked(False)
                self.tbRun.blockSignals(False)
                self._setup_icon(False)
                return
        else:
            port_name = self._get_port_name()

        self.leName.setDisabled(toggled)
        self.cbxComPort.setDisabled(toggled)
        self.tbRefreshPorts.setDisabled(toggled)
        self.name = self.leName.text().strip() if toggled else self.name

        if toggled:
            config = ScannerConfig(
                name=self.name,
                port_name=port_name,
                config=self._params,
            ).to_serial_port_config()
            if not self._verify_port_available(config):
                self.tbRun.blockSignals(True)
                self.tbRun.setChecked(False)
                self.tbRun.blockSignals(False)
                self._setup_icon(False)
                self.leName.setDisabled(False)
                self.cbxComPort.setDisabled(False)
                self.tbRefreshPorts.setDisabled(False)
                return
            self._scanner.start(self.name, config)
            self._scheduler.start(self.send_data)
            self._log.info("[%s] Сканер запущен на %s", self.name, port_name)
        else:
            self._scheduler.stop()
            self._scanner.stop()
            self.clear_data()
            self._log.info("[%s] Сканер остановлен", self.name)

    def load_options(self, params: ScannerParams) -> None:
        """Загружает параметры линии COM из сохранённой конфигурации.

        Args:
            params: Параметры скорости, parity и суффикса штрихкода.
        """
        self._params = params

    def options(self) -> ScannerConfig:
        """Возвращает текущую конфигурацию виджета для сохранения в JSON.

        Returns:
            Имя, COM-порт и параметры линии.
        """
        return ScannerConfig(
            name=self.name,
            port_name=self._get_port_name(),
            config=self._params,
        )
