import logging
import sys

from PySide6.QtWidgets import QApplication

from core.main_ui.line_emul import MainLineField
from libs.loggers import LOGGERS


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


if __name__ == '__main__':
    setup_logging()
    app = QApplication(sys.argv)
    pw = MainLineField()
    pw.show()
    app.exec()
