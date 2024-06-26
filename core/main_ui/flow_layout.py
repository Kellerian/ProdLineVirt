from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtWidgets import QLayout, QSizePolicy, QWidget, QWidgetItem


class FlowLayout(QLayout):
    widthChanged = Signal(int)

    def __init__(
        self, parent=None, spacing=6, orientation=Qt.Orientation.Horizontal
    ):
        super(FlowLayout, self).__init__(parent)

        self.setSpacing(spacing)
        self.orientation = orientation
        self.totalMaxWidth = 0
        self.itemsOnWidestRow = 0
        self.__items = list[QWidgetItem]()

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QWidgetItem):
        self.__items.append(item)

    def insertWidget(self, position: int, widget: QWidget):
        qwi = QWidgetItem(widget)
        self.__items.insert(position, qwi)
        self.addChildWidget(widget)

    def count(self):
        return len(self.__items)

    def itemAt(self, index):
        return self.__items[index] if 0 <= index < len(self.__items) else None

    def takeAt(self, index):
        return self.__items.pop(
            index
        ) if 0 <= index < len(self.__items) else None

    def expandingDirections(self):
        return Qt.Orientation.Vertical | Qt.Orientation.Horizontal

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width) -> int:
        if self.orientation == Qt.Orientation.Horizontal:
            return self.doLayoutHorizontal(QRect(0, 0, width, 0), True)
        elif self.orientation == Qt.Orientation.Vertical:
            return self.doLayoutVertical(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        if self.orientation == Qt.Orientation.Horizontal:
            self.doLayoutHorizontal(rect, False)
        elif self.orientation == Qt.Orientation.Vertical:
            self.doLayoutVertical(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()

        for item in self.__items:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayoutHorizontal(self, rect, test_only) -> int:
        # Get initial coordinates of the drawing region (should be 0, 0)
        x = rect.x()
        y = rect.y()
        line_height = 0
        i = 0
        for item in self.__items:
            wid = item.widget()
            if wid.isHidden():
                continue
            # Space X and Y is item spacing horizontally and vertically
            space_x = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal
            )
            space_y = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical
            )
            # Determine the coordinate we want to place the item at
            # It should be placed at : initial coordinate
            # of the rect + width of the item + spacing
            next_x = x + item.sizeHint().width() + space_x
            # If the calculated nextX is greater than the outer bound...
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()  # Reset X coordinate to origin of drawing region
                # Move Y coordinate to the next line
                y = y + line_height + space_y
                # Recalculate nextX based on the new X coordinate
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x  # Store the next starting X coordinate for next item
            line_height = max(line_height, item.sizeHint().height())
            i = i + 1
        return y + line_height - rect.y()

    def doLayoutVertical(self, rect, test_only) -> int:
        # Get initial coordinates of the drawing region (should be 0, 0)
        x = rect.x()
        y = rect.y()
        # Initialize column width and line height
        column_width = 0
        line_height = 0

        # Space between items
        space_x = 0

        # Variables that will represent the
        # position of the widgets in a 2D Array
        i = 0
        j = 0
        for item in self.__items:
            wid = item.widget()
            if wid.isHidden():
                continue
            # Space X and Y is item spacing horizontally and vertically
            space_x = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal
            )
            space_y = self.spacing() + wid.style().layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical
            )
            # Determine the coordinate we want to place the item at
            # It should be placed at :
            # initial coordinate of the rect + width of the item + spacing
            next_y = y + item.sizeHint().height() + space_y
            # If the calculated nextY is greater than the outer bound,
            # move to the next column
            if next_y - space_y > rect.bottom() and column_width > 0:
                y = rect.y()  # Reset y coordinate to origin of drawing region
                # Move X coordinate to the next column
                x = x + column_width + space_x
                # Recalculate nextX based on the new X coordinate
                next_y = y + item.sizeHint().height() + space_y
                # Reset the column width
                column_width = 0

                # Set indexes of the item for the 2D array
                j += 1
                i = 0

            # Assign 2D array indexes
            item.x_index = i
            item.y_index = j

            # Only call setGeometry (which place the actual
            # widget using coordinates) if testOnly is false
            # For some reason, Qt framework calls the
            # doLayout methods with testOnly set to true (WTF ??)
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            y = next_y  # Store the next starting Y coordinate for next item
            # Update the width of the column
            column_width = max(column_width, item.sizeHint().width())
            # Update the height of the line
            line_height = max(line_height, item.sizeHint().height())

            i += 1  # Increment i

        # Only call setGeometry (which place the actual
        # widget using coordinates) if testOnly is false
        # For some reason, Qt framework calls the doLayout
        # methods with testOnly set to true (WTF ??)
        if not test_only:
            self.calculateMaxWidth(i)
            # print("Total width : " + str(totalWidth))
            # noinspection PyUnresolvedReferences
            self.widthChanged.emit(
                self.totalMaxWidth + space_x * self.itemsOnWidestRow
            )
            # self.widthChanged.emit(self.totalMaxWidth)
        return line_height

    def calculateMaxWidth(self, number_of_rows):
        # Init variables
        self.totalMaxWidth = 0
        self.itemsOnWidestRow = 0

        # For each "row", calculate the total width
        # by adding the width of each item
        # and then update the totalMaxWidth if the
        # calculated width is greater than the current value
        # Also update the number of items on the widest row
        for i in range(number_of_rows):
            row_width = 0
            items_on_widest_row = 0
            for item in self.__items:
                if item.widget().isHidden():
                    continue
                # Only compare items from the same row
                # noinspection PyUnresolvedReferences
                if item.x_index == i:
                    row_width += item.sizeHint().width()
                    items_on_widest_row += 1
                if row_width > self.totalMaxWidth:
                    self.totalMaxWidth = row_width
                    self.itemsOnWidestRow = items_on_widest_row
