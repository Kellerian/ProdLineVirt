from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtCore import Qt


class CustomItemModel(QStandardItemModel):
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.isValid():
            flags &= Qt.ItemFlag.ItemIsDropEnabled
        return flags


def update_model_data(model: QStandardItemModel, data: list[str]):
    model.clear()
    for row in data:
        model.appendRow(QStandardItem(row))
