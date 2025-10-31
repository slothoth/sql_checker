from PyQt5.QtCore import Qt, QRectF, QLineF, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QFont, QPainterPath

from PyQt5.QtWidgets import (QGraphicsView, QGraphicsItem, QGraphicsObject, QGraphicsTextItem,
                             QGraphicsLineItem, QDialog, QFormLayout, QLineEdit, QDialogButtonBox)


class NodeEditDialog(QDialog):
    def __init__(self, text1, text2, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Node")
        self.text1_edit = QLineEdit(text1)
        self.text2_edit = QLineEdit(text2)
        layout = QFormLayout(self)
        layout.addRow("Field 1:", self.text1_edit)
        layout.addRow("Field 2:", self.text2_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        return self.text1_edit.text(), self.text2_edit.text()


class EdgeItem(QGraphicsLineItem):
    def __init__(self, start_node, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        self.setPen(QPen(QColor("#333"), 2))
        self.setZValue(-1)
        self.start_node.position_changed.connect(self.update_position)
        self.end_node.position_changed.connect(self.update_position)
        self.update_position()

    def update_position(self):
        line = QLineF(self.start_node.sceneBoundingRect().center(), self.end_node.sceneBoundingRect().center())
        self.setLine(line)


class NodeItem(QGraphicsObject):
    position_changed = pyqtSignal()
    NODE_WIDTH = 150
    NODE_HEIGHT = 70
    HEADER_HEIGHT = 25
    PADDING = 5

    def __init__(self, node_id, text1="Title", text2="Description", parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.edges = []
        self.text1_item = QGraphicsTextItem(self)
        self.text1_item.setPlainText(text1)
        self.text1_item.setDefaultTextColor(Qt.white)
        self.text1_item.setFont(QFont("Inter", 10, QFont.Bold))
        self.text1_item.setTextWidth(self.NODE_WIDTH - 2 * self.PADDING)
        self.text1_item.setPos(self.PADDING, self.PADDING / 2)
        self.text2_item = QGraphicsTextItem(self)
        self.text2_item.setPlainText(text2)
        self.text2_item.setDefaultTextColor(Qt.black)
        self.text2_item.setFont(QFont("Inter", 9))
        self.text2_item.setTextWidth(self.NODE_WIDTH - 2 * self.PADDING)
        self.text2_item.setPos(self.PADDING, self.HEADER_HEIGHT + self.PADDING)

    def boundingRect(self):
        return QRectF(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT).adjusted(-1, -1, 1, 1)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 8, 8)
        painter.setBrush(QBrush(QColor("#4a90e2")))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.NODE_WIDTH, self.HEADER_HEIGHT, 8, 8)
        path.addRect(0, self.HEADER_HEIGHT - 8, self.NODE_WIDTH, 8)
        painter.drawPath(path)
        if self.isSelected():
            painter.setPen(QPen(QColor("#f5a623"), 2, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, self.NODE_WIDTH, self.NODE_HEIGHT, 8, 8)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.position_changed.emit()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        dialog = NodeEditDialog(self.text1_item.toPlainText(), self.text2_item.toPlainText())
        if dialog.exec_() == QDialog.Accepted:
            text1, text2 = dialog.get_data()
            self.text1_item.setPlainText(text1)
            self.text2_item.setPlainText(text2)
        super().mouseDoubleClickEvent(event)


class GraphView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
