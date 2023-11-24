from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QListView


class DropListView(QListView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setModel(QStandardItemModel(0, 1))

    def dragEnterEvent(self, event):
        event.accept() if event.mimeData().hasText() else event.ignore()

    def dragMoveEvent(self, event):
        event.accept() if event.mimeData().hasText() else event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.CopyAction)
            self.model().appendRow(QStandardItem(event.mimeData().text()))
            event.accept()
        else:
            event.ignore()
