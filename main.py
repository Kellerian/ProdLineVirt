import logging
import sys
from pathlib import Path

import client_info

from PySide6.QtWidgets import QApplication

from core.main_ui.line_emul import MainLineField
from core.main_ui.user_settings import load_user_settings
from libs.loggers import LOGGERS
from libs.qt_theme import ThemeMode, apply_theme


def setup_logging():
    for logger in LOGGERS:
        root = logging.getLogger(logger)
        root.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(name)s][%(levelname)s]:'
                ' %(message)s', datefmt='%d.%m.%Y %H:%M:%S'
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)


def setup_pathes():
    client_info.RUNDIR = Path(__file__).parent
    cur_path = Path(__file__).parent
    if getattr(sys, 'frozen', False):
        cur_path = Path(sys.executable).parent
    client_info.WORKDIR = cur_path


if __name__ == '__main__':
    import os
    import platform

    if platform.system() == 'Linux':
        os.environ['QT_QPA_PLATFORM'] = "xcb"
    elif platform.system() == "Windows":
        # Disable Qt native dark title bars so global QSS controls menu/combo popups
        # (light theme uses windowsvista style; see libs/qt_theme.apply_qt_style).
        os.environ['QT_QPA_PLATFORM'] = "windows:darkmode=0"
    setup_pathes()
    setup_logging()
    app = QApplication(sys.argv)
    user_settings = load_user_settings()
    apply_theme(app, ThemeMode(user_settings.theme_preference))
    pw = MainLineField()
    pw.show()
    app.exec()
