from PyQt6.QtGui import QStandardItem, QStandardItemModel


def update_model_data(model: QStandardItemModel, data: list[str]):
    model.clear()
    for row in data:
        model.appendRow(QStandardItem(row))
