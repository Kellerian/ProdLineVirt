"""Настройка Qt-стиля приложения для корректной светлой темы."""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


def apply_light_theme(app: QApplication) -> None:
    """Применить светлую тему Qt к приложению.

    На Windows при системной тёмной теме и ``QT_QPA_PLATFORM=windows:darkmode=0``
    дефолтный стиль Windows 11 (Qt 6.7) некорректно рендерит popup-меню и
    выпадающие списки QComboBox. Стиль ``windowsvista`` устраняет эту проблему.

    На Linux стиль не меняется.

    Args:
        app: Экземпляр QApplication, созданный до показа главного окна.
    """
    if platform.system() == "Windows":
        app.setStyle("windowsvista")
